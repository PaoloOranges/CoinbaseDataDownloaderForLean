"""
Data handling module
Handles saving and loading data in CSV format
"""

import csv
import logging
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils import normalize_symbol, parse_iso_datetime


class DataHandler:
    """Handles data I/O operations."""
    
    def __init__(self):
        """Initialize the data handler."""
        self.logger = logging.getLogger(__name__)
    
    def save_quotes_to_csv(self, quotes: List[Dict[str, Any]], filepath: Path) -> None:
        """
        Save quote (candle/OHLC) data to a CSV file.
        
        Args:
            quotes: List of quote dictionaries
            filepath: Path to save the CSV file
        """
        if not quotes:
            self.logger.warning(f"No quotes to save to {filepath}")
            return
        
        try:
            filepath = Path(filepath)
            
            fieldnames = ['symbol', 'time', 'open', 'high', 'low', 'close', 'volume']
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for quote in quotes:
                    writer.writerow({
                        'symbol': quote.get('symbol', ''),
                        'time': quote.get('time', ''),
                        'open': quote.get('open', ''),
                        'high': quote.get('high', ''),
                        'low': quote.get('low', ''),
                        'close': quote.get('close', ''),
                        'volume': quote.get('volume', '')
                    })
            
            self.logger.info(f"Saved {len(quotes)} quotes to {filepath}")
            
        except IOError as e:
            self.logger.error(f"Failed to write quotes to {filepath}: {e}")
            raise
    
    def save_quotes_by_day(self, quotes: List[Dict[str, Any]], output_dir: Path, granularity: str, keep_csv: bool = False) -> None:
        """
        Save quote data with granularity-based folder structure and ZIP compression.
        
        Args:
            quotes: List of quote dictionaries
            output_dir: Output directory path
            granularity: Granularity string ('MINUTE', 'HOUR', 'DAILY')
            keep_csv: If True, keep CSV files after compression; if False, delete them
        """
        if not quotes:
            self.logger.warning("No quotes to save")
            return
        
        quotes_by_date: Dict[str, List[Tuple[Any, Dict[str, Any]]]] = defaultdict(list)
        for quote in quotes:
            time_str = quote.get('time', '')
            dt = parse_iso_datetime(time_str)
            date_key = dt.strftime('%Y%m%d')
            quotes_by_date[date_key].append((dt, quote))
        
        symbol = quotes[0].get('symbol', 'unknown')
        symbol_clean = normalize_symbol(symbol)
        granularity_lower = granularity.lower()
        
        granularity_folder = output_dir / granularity_lower
        granularity_folder.mkdir(parents=True, exist_ok=True)
        
        if granularity == 'MINUTE':
            base_folder = granularity_folder / symbol_clean
            base_folder.mkdir(parents=True, exist_ok=True)
        else:
            base_folder = granularity_folder
        
        saved_zips = 0
        temp_csv_files: List[Tuple[Path, str]] = []
        
        for date_str, day_items in quotes_by_date.items():
            try:
                day_items.sort(key=lambda pair: pair[0])
                if granularity == 'MINUTE':
                    csv_filename = f"{date_str}_{symbol_clean}_minute_trade.csv"
                    csv_filepath = base_folder / csv_filename
                    self._write_csv(csv_filepath, day_items, granularity)
                    
                    zip_filename = f"{date_str}_trade.zip"
                    zip_filepath = base_folder / zip_filename
                    self._zip_files(zip_filepath, [(csv_filepath, csv_filename)])
                    
                    if not keep_csv:
                        csv_filepath.unlink()
                        self.logger.debug(f"Deleted temporary CSV: {csv_filepath}")
                    
                    saved_zips += 1
                else:
                    csv_filename = f"{date_str}_{symbol_clean}_{granularity_lower}_trade.csv"
                    csv_filepath = base_folder / csv_filename
                    self._write_csv(csv_filepath, day_items, granularity)
                    temp_csv_files.append((csv_filepath, csv_filename))
                    self.logger.debug(f"Created temporary CSV: {csv_filename}")
            except Exception as e:
                self.logger.error(f"Failed to process {date_str}: {e}")
        
        if granularity != 'MINUTE' and temp_csv_files:
            zip_filename = f"{symbol_clean}_trade.zip"
            zip_filepath = base_folder / zip_filename
            try:
                self._zip_files(zip_filepath, temp_csv_files)
                self.logger.info(f"Saved {sum(len(items) for items in quotes_by_date.values())} quotes to {zip_filepath}")
                if not keep_csv:
                    for csv_filepath, _ in temp_csv_files:
                        csv_filepath.unlink()
                        self.logger.debug(f"Deleted temporary CSV: {csv_filepath}")
                saved_zips += 1
            except Exception as e:
                self.logger.error(f"Failed to create {granularity_lower} ZIP file for {symbol}: {e}")
        
        self.logger.info(f"Total: saved {len(quotes)} quotes in {saved_zips} ZIP file(s)")
    
    def _write_csv(self, filepath: Path, items: List[Tuple[Any, Dict[str, Any]]], granularity: str) -> None:
        filepath = Path(filepath)
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for dt, quote in items:
                writer.writerow(self._build_csv_row(dt, quote, granularity))
    
    def _build_csv_row(self, dt: Any, quote: Dict[str, Any], granularity: str) -> List[Any]:
        if granularity == 'MINUTE':
            start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            time_value = str(int((dt - start_of_day).total_seconds() * 1000))
        else:
            time_value = dt.strftime('%Y%m%d %H:%M')
        return [
            time_value,
            quote.get('open', ''),
            quote.get('high', ''),
            quote.get('low', ''),
            quote.get('close', ''),
            quote.get('volume', '')
        ]
    
    def _zip_files(self, zip_filepath: Path, file_entries: List[Tuple[Path, str]]) -> None:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for csv_filepath, csv_filename in file_entries:
                zipf.write(csv_filepath, arcname=csv_filename)
    
    def load_quotes_from_csv(self, filepath: Path) -> List[Dict[str, Any]]:
        """
        Load quote (candle/OHLC) data from a CSV file.
        
        Args:
            filepath: Path to the CSV file
        
        Returns:
            List of quote dictionaries
        """
        quotes = []
        
        try:
            filepath = Path(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    quotes.append({
                        'symbol': row['symbol'],
                        'time': row['time'],
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume'])
                    })
            
            self.logger.info(f"Loaded {len(quotes)} quotes from {filepath}")
            return quotes
        except IOError as e:
            self.logger.error(f"Failed to read quotes from {filepath}: {e}")
            raise
