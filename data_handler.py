"""
Data handling module
Handles saving and loading data in CSV format
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any


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
