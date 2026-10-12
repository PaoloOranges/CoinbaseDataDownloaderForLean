"""
Coinbase API interaction module
Handles downloading quote data from Coinbase
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from coinbase_downloader.downloader.base import BaseDownloader
from coinbase_downloader.utils.utils import normalize_symbol, validate_symbol_format


class CoinbaseDownloader(BaseDownloader):
    """Handles downloading data from Coinbase APIs."""

    BASE_URL = "https://api.exchange.coinbase.com"
    MAX_CANDLES_PER_REQUEST = 300
    MAX_REQUESTS_PER_SECOND = 15
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.5
    CACHE_TTL_SECONDS = 300

    @property
    def default_symbols_file(self) -> str:
        return 'coinbase-download-symbols.txt'

    @property
    def timestamps_filename(self) -> str:
        return 'coinbase-download-last-timestamps.json'

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return normalize_symbol(symbol)

    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid using cached product metadata."""
        try:
            return symbol in self.get_available_symbols()
        except requests.exceptions.RequestException:
            return validate_symbol_format(symbol)

    def get_available_symbols(self) -> List[str]:
        """
        Fetch all available trading pairs from Coinbase.
        
        Returns:
            List of symbol strings (e.g., ['BTC-USD', 'ETH-EUR'])
        """
        now = time.monotonic()
        if self._symbols_cache and now - self._symbols_cache_time < self.CACHE_TTL_SECONDS:
            self.logger.debug("Returning cached Coinbase symbols")
            return self._symbols_cache
        
        try:
            self.logger.debug("Fetching available products from Coinbase...")
            response = self._request_with_retry('GET', f"{self.BASE_URL}/products")
            products = response.json()
            symbols = [
                p['id'] for p in products
                if p.get('quote_currency') and p.get('trading_disabled') is False
            ]
            self._symbols_cache = sorted(symbols)
            self._symbols_cache_time = now
            self.logger.info(f"Found {len(self._symbols_cache)} available symbols")
            return self._symbols_cache
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch products: {e}")
            raise
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid using cached product metadata."""
        try:
            return symbol in self.get_available_symbols()
        except requests.exceptions.RequestException:
            return False
    
    def get_historical_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        granularity: int = 60
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Download historical quote data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USD')
            start_time: Start datetime for historical data
            end_time: End datetime for historical data
            granularity: Candle granularity in seconds (60, 300, 900, 3600, 21600, 86400)
        
        Returns:
            Tuple of (list of quote dictionaries containing historical data, max timestamp string)
        """
        self.logger.info(f"Fetching historical data for {symbol} from {start_time} to {end_time}")
        
        if not self._is_valid_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        try:
            quotes = self._fetch_candles(symbol, start_time, end_time, granularity)
            self.logger.info(f"Fetched {len(quotes)} quote candles for {symbol}")
            max_timestamp = max((q['time'] for q in quotes), default=None) if quotes else None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for {symbol}: {e}")
            raise
        
        return quotes, max_timestamp
    
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
        candles: List[Dict[str, Any]] = []
        current_time = start_time
        
        while current_time < end_time:
            batch_end = min(
                current_time + timedelta(seconds=self.MAX_CANDLES_PER_REQUEST * granularity),
                end_time
            )
            
            params = {
                'start': current_time.isoformat(),
                'end': batch_end.isoformat(),
                'granularity': granularity
            }
            self.logger.debug(f"Fetching candles for {symbol}: {current_time} to {batch_end}")
            response = self._request_with_retry(
                'GET',
                f"{self.BASE_URL}/products/{symbol}/candles",
                params=params
            )
            batch_candles = response.json()
            
            for candle in batch_candles:
                candles.append({
                    'symbol': symbol,
                    'time': datetime.fromtimestamp(candle[0], tz=timezone.utc).isoformat(),
                    'low': float(candle[1]),
                    'high': float(candle[2]),
                    'open': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            current_time = batch_end
        
        return candles
