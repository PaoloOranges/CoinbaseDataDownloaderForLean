"""
Data handling module
Handles saving and loading data in CSV format
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List


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
            
            # Define CSV columns
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
    
    def save_quotes_by_day(self, quotes: List[Dict[str, Any]], output_dir: Path, granularity: str) -> None:
        """
        Save quote data split by day with new filename format.
        
        Args:
            quotes: List of quote dictionaries
            output_dir: Output directory path
            granularity: Granularity string ('MINUTE', 'HOUR', 'DAY')
        """
        if not quotes:
            self.logger.warning("No quotes to save")
            return
        
        from collections import defaultdict
        from datetime import datetime
        
        # Group quotes by date
        quotes_by_date = defaultdict(list)
        for quote in quotes:
            # Parse the time string to get date
            time_str = quote.get('time', '')
            if 'T' in time_str:
                # ISO format: 2024-01-01T10:00:00Z
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                # Assume it's already a date string
                dt = datetime.strptime(time_str, '%Y-%m-%d')
            date_key = dt.strftime('%Y%m%d')
            quotes_by_date[date_key].append(quote)
        
        # Get symbol from first quote
        symbol = quotes[0].get('symbol', 'unknown')
        symbol_clean = symbol.lower().replace('-', '')
        
        # Map granularity to lowercase string
        granularity_lower = granularity.lower()
        
        saved_files = 0
        
        for date_str, day_quotes in quotes_by_date.items():
            try:
                # Sort quotes by time (chronological order)
                day_quotes.sort(key=lambda q: q.get('time', ''))
                
                # Create filename
                filename = f"{date_str}_{symbol_clean}_{granularity_lower}_trade.csv"
                filepath = output_dir / filename
                
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    for quote in day_quotes:
                        if granularity == 'MINUTE':
                            # TIME_OF_DAY_MILLISECONDS,open,high,low,close,volume
                            time_str = quote.get('time', '')
                            if 'T' in time_str:
                                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                                # Convert to milliseconds since start of day
                                start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                                milliseconds = int((dt - start_of_day).total_seconds() * 1000)
                                time_value = str(milliseconds)
                            else:
                                time_value = time_str
                        else:
                            # yyyyMMdd HH:mm,open,high,low,close,volume
                            time_str = quote.get('time', '')
                            if 'T' in time_str:
                                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                                time_value = dt.strftime('%Y%m%d %H:%M')
                            else:
                                time_value = time_str
                        
                        writer.writerow([
                            time_value,
                            quote.get('open', ''),
                            quote.get('high', ''),
                            quote.get('low', ''),
                            quote.get('close', ''),
                            quote.get('volume', '')
                        ])
                
                self.logger.info(f"Saved {len(day_quotes)} quotes to {filename}")
                saved_files += 1
                
            except IOError as e:
                self.logger.error(f"Failed to write quotes for {date_str}: {e}")
        
        self.logger.info(f"Total: saved {len(quotes)} quotes across {saved_files} files")
    
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
