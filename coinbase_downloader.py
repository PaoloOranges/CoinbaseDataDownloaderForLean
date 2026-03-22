"""
Coinbase API interaction module
Handles downloading quote data from Coinbase
"""

import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple
import time


class CoinbaseDownloader:
    """Handles downloading data from Coinbase APIs."""
    
    BASE_URL = "https://api.exchange.coinbase.com"
    
    def __init__(self):
        """Initialize the Coinbase downloader."""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CoinbaseDataDownloader/1.0'
        })
    
    def get_available_symbols(self) -> List[str]:
        """
        Fetch all available trading pairs from Coinbase.
        
        Returns:
            List of symbol strings (e.g., ['BTC-USD', 'ETH-EUR'])
        """
        try:
            self.logger.debug("Fetching available products from Coinbase...")
            response = self.session.get(f"{self.BASE_URL}/products")
            response.raise_for_status()
            
            products = response.json()
            
            # Filter for products that are currently trading
            symbols = [
                p['id'] for p in products 
                if p.get('quote_currency') and p.get('trading_disabled') is False
            ]
            
            self.logger.info(f"Found {len(symbols)} available symbols")
            return sorted(symbols)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch products: {e}")
            raise
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid."""
        try:
            response = self.session.get(f"{self.BASE_URL}/products/{symbol}")
            return response.status_code == 200
        except:
            return False
    
    def get_historical_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        granularity: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Download historical quote data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USD')
            start_time: Start datetime for historical data
            end_time: End datetime for historical data
            granularity: Candle granularity in seconds (60, 300, 900, 3600, 21600, 86400)
        
        Returns:
            List of quote dictionaries containing historical data
        """
        self.logger.info(f"Fetching historical data for {symbol} from {start_time} to {end_time}")
        
        # Validate symbol
        if not self._is_valid_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        try:
            # Fetch candles (OHLC data) which represents price movements
            quotes = self._fetch_candles(symbol, start_time, end_time, granularity)
            self.logger.info(f"Fetched {len(quotes)} quote candles for {symbol}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for {symbol}: {e}")
            raise
        
        return quotes
    
    def _fetch_candles(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        granularity: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLC candle data (quotes).
        
        Args:
            symbol: Trading pair
            start_time: Start datetime
            end_time: End datetime
            granularity: Candle granularity in seconds
        
        Returns:
            List of candle dictionaries
        """
        candles = []
        current_time = start_time
        
        while current_time < end_time:
            # Coinbase API returns max 300 candles per request
            batch_end = min(
                datetime.fromtimestamp(current_time.timestamp() + 300 * granularity),
                end_time
            )
            
            try:
                params = {
                    'start': current_time.isoformat(),
                    'end': batch_end.isoformat(),
                    'granularity': granularity
                }
                
                self.logger.debug(f"Fetching candles for {symbol}: {current_time} to {batch_end}")
                response = self.session.get(
                    f"{self.BASE_URL}/products/{symbol}/candles",
                    params=params
                )
                response.raise_for_status()
                
                batch_candles = response.json()
                
                # Parse candle data
                for candle in batch_candles:
                    candles.append({
                        'symbol': symbol,
                        'time': datetime.fromtimestamp(candle[0]).isoformat(),
                        'low': float(candle[1]),
                        'high': float(candle[2]),
                        'open': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    })
                
                # Rate limiting - Coinbase allows 15 requests per second
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Failed to fetch candles batch: {e}")
                # Continue to next batch
            
            current_time = batch_end
        
        return candles
    

