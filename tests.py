"""
Unit tests for Coinbase Data Downloader
Run with: python -m pytest tests/ -v
"""

import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from coinbase_downloader import CoinbaseDownloader
from data_handler import DataHandler
from utils import (
    format_bytes,
    format_number,
    get_date_range_description,
    normalize_symbol,
    parse_datetime,
    validate_datetime_format,
    validate_symbol_format,
)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_parse_datetime_valid(self):
        self.assertEqual(parse_datetime("20240101-00:00:00"), datetime(2024, 1, 1, 0, 0, 0))

    def test_parse_datetime_invalid(self):
        with self.assertRaises(ValueError):
            parse_datetime("2024-01-01 00:00:00")

    def test_normalize_symbol(self):
        self.assertEqual(normalize_symbol("BTC-USD"), "btcusd")
        self.assertEqual(normalize_symbol("ETH-EUR"), "etheur")

    def test_validate_datetime_format_valid(self):
        """Test valid datetime formats."""
        self.assertTrue(validate_datetime_format("20240101-00:00:00"))
        self.assertTrue(validate_datetime_format("20241231-23:59:59"))
        self.assertTrue(validate_datetime_format("20240615-14:30:45"))
    
    def test_validate_datetime_format_invalid(self):
        """Test invalid datetime formats."""
        self.assertFalse(validate_datetime_format("2024-01-01 00:00:00"))
        self.assertFalse(validate_datetime_format("01/01/2024-00:00:00"))
        self.assertFalse(validate_datetime_format("20240101"))
        self.assertFalse(validate_datetime_format("20240101-00:00"))
    
    def test_validate_symbol_format_valid(self):
        """Test valid symbol formats."""
        self.assertTrue(validate_symbol_format("BTC-USD"))
        self.assertTrue(validate_symbol_format("ETH-EUR"))
        self.assertTrue(validate_symbol_format("XRP-GBP"))
        self.assertTrue(validate_symbol_format("USDC-USD"))
    
    def test_validate_symbol_format_invalid(self):
        """Test invalid symbol formats."""
        self.assertFalse(validate_symbol_format("BTC_USD"))
        self.assertFalse(validate_symbol_format("btc-usd"))  # lowercase
        self.assertFalse(validate_symbol_format("BTC-"))
        self.assertFalse(validate_symbol_format("BTCUSD"))
    
    def test_format_bytes(self):
        """Test byte formatting."""
        self.assertEqual(format_bytes(512), "512.00 B")
        self.assertEqual(format_bytes(1536), "1.50 KB")
        self.assertEqual(format_bytes(1048576), "1.00 MB")
        self.assertEqual(format_bytes(1073741824), "1.00 GB")
    
    def test_format_number(self):
        """Test number formatting."""
        self.assertEqual(format_number(1234.567), "1,234.57")
        self.assertEqual(format_number(1000000), "1,000,000.00")
        self.assertEqual(format_number(123.4, 3), "123.400")
    
    def test_get_date_range_description(self):
        """Test date range description."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 6, 3, 30, 0)
        
        result = get_date_range_description(start, end)
        self.assertIn("5 days", result)
        self.assertIn("3 hours", result)


class TestDataHandler(unittest.TestCase):
    """Test data handler functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = DataHandler()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_quotes(self):
        """Test saving and loading quotes."""
        quotes = [
            {
                'symbol': 'ETH-USD',
                'time': '2024-01-01T10:00:00Z',
                'open': 2000.00,
                'high': 2050.00,
                'low': 1990.00,
                'close': 2040.00,
                'volume': 100.5
            }
        ]
        
        csv_path = Path(self.temp_dir) / "test_quotes.csv"
        
        # Save and load
        self.handler.save_quotes_to_csv(quotes, csv_path)
        loaded = self.handler.load_quotes_from_csv(csv_path)
        
        # Verify
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]['symbol'], 'ETH-USD')
        self.assertEqual(loaded[0]['close'], 2040.0)


class TestCoinbaseDownloader(unittest.TestCase):
    """Test Coinbase downloader batching and retry behavior."""

    def test_request_with_retry_retries_and_succeeds(self):
        downloader = CoinbaseDownloader()
        first_response = Mock()
        first_response.status_code = 500
        first_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")

        second_response = Mock()
        second_response.status_code = 200
        second_response.raise_for_status.return_value = None
        second_response.json.return_value = []

        with patch.object(downloader, '_throttle', return_value=None), \
                patch.object(downloader.session, 'request', side_effect=[first_response, second_response]) as mock_request:
            response = downloader._request_with_retry('GET', downloader.BASE_URL + '/products')
            self.assertEqual(mock_request.call_count, 2)
            self.assertEqual(response.json(), [])

    def test_get_available_symbols_uses_cache(self):
        downloader = CoinbaseDownloader()
        product_list = [{'id': 'BTC-USD', 'quote_currency': 'USD', 'trading_disabled': False}]

        successful_response = Mock()
        successful_response.status_code = 200
        successful_response.raise_for_status.return_value = None
        successful_response.json.return_value = product_list

        with patch.object(downloader, '_throttle', return_value=None), \
                patch.object(downloader.session, 'request', return_value=successful_response) as mock_request:
            symbols_first = downloader.get_available_symbols()
            symbols_second = downloader.get_available_symbols()

            self.assertEqual(symbols_first, ['BTC-USD'])
            self.assertEqual(symbols_second, ['BTC-USD'])
            self.assertEqual(mock_request.call_count, 1)

    def test_fetch_candles_batches_multiple_requests(self):
        downloader = CoinbaseDownloader()
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = start + timedelta(minutes=301)

        first_response = Mock()
        first_response.json.return_value = [[int(start.timestamp()), 100, 110, 90, 105, 1000]]
        second_response = Mock()
        second_response.json.return_value = [[int((start + timedelta(minutes=300)).timestamp()), 101, 111, 91, 106, 1100]]

        with patch.object(downloader, '_throttle', return_value=None), \
                patch.object(downloader, '_request_with_retry', side_effect=[first_response, second_response]) as mock_request:
            candles = downloader._fetch_candles('BTC-USD', start, end, 60)
            self.assertEqual(len(candles), 2)
            self.assertEqual(mock_request.call_count, 2)


class TestCompressionAndFolderStructure(unittest.TestCase):
    """Test new compression and folder structure features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = DataHandler()
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_quotes(self, symbol, date_str, hour_count=3):
        """Create sample quotes for testing."""
        quotes = []
        for hour in range(hour_count):
            for minute in range(0, 60, 15):  # Every 15 minutes
                dt = datetime.strptime(f"{date_str}T{hour:02d}:{minute:02d}:00", '%Y-%m-%dT%H:%M:%S')
                quotes.append({
                    'symbol': symbol,
                    'time': dt.isoformat() + 'Z',
                    'open': 100.0 + hour,
                    'high': 110.0 + hour,
                    'low': 90.0 + hour,
                    'close': 105.0 + hour,
                    'volume': 1000 + hour*100
                })
        return quotes
    
    def test_minute_granularity_folder_structure(self):
        """Test MINUTE granularity creates correct folder structure."""
        quotes = self.create_sample_quotes('ETH-EUR', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=False)
        
        # Check folder structure: minute/etheur/
        minute_folder = self.output_path / 'minute'
        etheur_folder = minute_folder / 'etheur'
        
        self.assertTrue(minute_folder.exists(), "minute folder not created")
        self.assertTrue(etheur_folder.exists(), "etheur subfolder not created")
    
    def test_minute_granularity_zip_files(self):
        """Test MINUTE granularity creates daily ZIP files."""
        quotes = self.create_sample_quotes('BTC-EUR', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=False)
        
        # Check ZIP file exists: minute/btceur/20240101_trade.zip
        zip_path = self.output_path / 'minute' / 'btceur' / '20240101_trade.zip'
        
        self.assertTrue(zip_path.exists(), f"ZIP file not found: {zip_path}")
        self.assertTrue(zipfile.is_zipfile(zip_path), "File is not a valid ZIP")
    
    def test_minute_multiple_days_multiple_zips(self):
        """Test MINUTE granularity with multiple days creates multiple ZIPs."""
        # Create quotes for 3 days
        quotes = []
        for day in [1, 2, 3]:
            day_str = f'2024-01-{day:02d}'
            quotes.extend(self.create_sample_quotes('ETH-EUR', day_str, hour_count=2))
        
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=False)
        
        # Check that 3 ZIP files were created
        etheur_folder = self.output_path / 'minute' / 'etheur'
        zip_files = list(etheur_folder.glob('*_trade.zip'))
        
        self.assertEqual(len(zip_files), 3, f"Expected 3 ZIP files, found {len(zip_files)}")
        
        # Verify filenames
        expected_zips = {'20240101_trade.zip', '20240102_trade.zip', '20240103_trade.zip'}
        actual_zips = {z.name for z in zip_files}
        self.assertEqual(actual_zips, expected_zips, "ZIP filenames don't match expected pattern")
    
    def test_minute_csv_deleted_by_default(self):
        """Test MINUTE granularity deletes CSVs by default."""
        quotes = self.create_sample_quotes('BTC-USD', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=False)
        
        # No CSV files should exist
        csv_files = list((self.output_path / 'minute' / 'btcusd').glob('*.csv'))
        self.assertEqual(len(csv_files), 0, f"CSV files should be deleted but found: {csv_files}")
    
    def test_minute_csv_kept_with_flag(self):
        """Test MINUTE granularity keeps CSVs with --keep-csv flag."""
        quotes = self.create_sample_quotes('BTC-USD', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=True)
        
        # CSV files should exist alongside ZIP
        btcusd_folder = self.output_path / 'minute' / 'btcusd'
        csv_files = list(btcusd_folder.glob('*.csv'))
        zip_files = list(btcusd_folder.glob('*.zip'))
        
        self.assertGreater(len(csv_files), 0, "CSV files should be kept but none found")
        self.assertGreater(len(zip_files), 0, "ZIP files should exist")
    
    def test_hour_granularity_folder_structure(self):
        """Test HOUR granularity creates hour folder."""
        quotes = self.create_sample_quotes('ETH-EUR', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'HOUR', keep_csv=False)
        
        # Check folder structure: hour/ (no symbol subfolder)
        hour_folder = self.output_path / 'hour'
        self.assertTrue(hour_folder.exists(), "hour folder not created")
        
        # No symbol subfolder should exist in hour
        symbol_folder = hour_folder / 'etheur'
        self.assertFalse(symbol_folder.exists(), "Symbol subfolder should not be created for HOUR")
    
    def test_hour_single_zip_per_symbol(self):
        """Test HOUR granularity creates single ZIP with all data for symbol."""
        quotes = self.create_sample_quotes('BTC-EUR', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'HOUR', keep_csv=False)
        
        # Check ZIP file: hour/btceur_trade.zip
        zip_path = self.output_path / 'hour' / 'btceur_trade.zip'
        
        self.assertTrue(zip_path.exists(), f"ZIP file not found: {zip_path}")
        self.assertTrue(zipfile.is_zipfile(zip_path), "File is not a valid ZIP")
        
        # Check that ZIP contains the CSV file
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            files = zipf.namelist()
            self.assertGreater(len(files), 0, "ZIP should contain CSV file")
            self.assertTrue(any('trade.csv' in f for f in files), "ZIP should contain trade CSV")
    
    def test_hour_multiple_days_single_zip(self):
        """Test HOUR granularity consolidates multiple days into single ZIP."""
        # Create quotes for 3 days
        quotes = []
        for day in [1, 2, 3]:
            day_str = f'2024-01-{day:02d}'
            quotes.extend(self.create_sample_quotes('ETH-USD', day_str, hour_count=2))
        
        self.handler.save_quotes_by_day(quotes, self.output_path, 'HOUR', keep_csv=False)
        
        # Check that only 1 ZIP file was created
        hour_folder = self.output_path / 'hour'
        zip_files = list(hour_folder.glob('*.zip'))
        
        self.assertEqual(len(zip_files), 1, f"Expected 1 ZIP file, found {len(zip_files)}")
        self.assertEqual(zip_files[0].name, 'ethusd_trade.zip')
        
        # Check that ZIP contains multiple CSVs (one per day)
        with zipfile.ZipFile(zip_files[0], 'r') as zipf:
            files = zipf.namelist()
            self.assertEqual(len(files), 3, f"Expected 3 CSV files in ZIP, found {len(files)}")
    
    def test_daily_granularity_folder_structure(self):
        """Test DAILY granularity creates daily folder."""
        quotes = self.create_sample_quotes('ETH-EUR', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'DAILY', keep_csv=False)
        
        # Check folder structure: daily/ (no symbol subfolder)
        daily_folder = self.output_path / 'daily'
        self.assertTrue(daily_folder.exists(), "daily folder not created")
        
        # No symbol subfolder should exist
        symbol_folder = daily_folder / 'etheur'
        self.assertFalse(symbol_folder.exists(), "Symbol subfolder should not be created for DAILY")
    
    def test_daily_single_zip_per_symbol(self):
        """Test DAILY granularity creates single ZIP with all data for symbol."""
        quotes = self.create_sample_quotes('BTC-USD', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'DAILY', keep_csv=False)
        
        # Check ZIP file: daily/btcusd_trade.zip
        zip_path = self.output_path / 'daily' / 'btcusd_trade.zip'
        
        self.assertTrue(zip_path.exists(), f"ZIP file not found: {zip_path}")
        self.assertTrue(zipfile.is_zipfile(zip_path), "File is not a valid ZIP")
    
    def test_zip_content_integrity(self):
        """Test that ZIP files contain correct CSV content."""
        quotes = self.create_sample_quotes('BTC-USD', '2024-01-01', hour_count=1)
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=False)
        
        # Open ZIP and verify content
        zip_path = self.output_path / 'minute' / 'btcusd' / '20240101_trade.zip'
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            files = zipf.namelist()
            self.assertEqual(len(files), 1, "ZIP should contain exactly one CSV file")
            
            # Verify CSV name
            csv_name = files[0]
            self.assertIn('trade.csv', csv_name)
            
            # Verify CSV can be read
            with zipf.open(csv_name) as f:
                content = f.read().decode('utf-8')
                lines = content.strip().split('\n')
                # Should have at least 4 lines (60min / 15min interval = 4 quotes)
                self.assertGreater(len(lines), 0, "CSV should contain data")
    
    def test_symbol_name_cleaning(self):
        """Test that symbol names are cleaned correctly (lowercase, no dash)."""
        quotes = self.create_sample_quotes('BTC-USD', '2024-01-01')
        self.handler.save_quotes_by_day(quotes, self.output_path, 'MINUTE', keep_csv=False)
        
        # Check that folder uses cleaned name: btcusd (not BTC-USD or btc-usd)
        btcusd_folder = self.output_path / 'minute' / 'btcusd'
        self.assertTrue(btcusd_folder.exists(), "Symbol folder should use cleaned name (btcusd)")
        
        # Check that ZIP filename uses cleaned name
        zip_path = self.output_path / 'minute' / 'btcusd' / '20240101_trade.zip'
        self.assertTrue(zip_path.exists(), "ZIP filename should use cleaned symbol name")


if __name__ == '__main__':
    unittest.main()
