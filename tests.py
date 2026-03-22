"""
Unit tests for Coinbase Data Downloader
Run with: python -m pytest tests/ -v
"""

import unittest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from utils import (
    validate_datetime_format,
    validate_symbol_format,
    format_bytes,
    format_number,
    get_date_range_description
)
from data_handler import DataHandler


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
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


if __name__ == '__main__':
    unittest.main()
