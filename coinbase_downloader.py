"""
Coinbase API interaction module
Handles downloading quote data from Coinbase
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests


class CoinbaseDownloader:
    """Handles downloading data from Coinbase APIs."""
    
    BASE_URL = "https://api.exchange.coinbase.com"
    MAX_CANDLES_PER_REQUEST = 300
    MAX_REQUESTS_PER_SECOND = 15
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.5
    CACHE_TTL_SECONDS = 300
    
    def __init__(self):
        """Initialize the Coinbase downloader."""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CoinbaseDataDownloader/1.0'
        })
        self._symbols_cache: Optional[List[str]] = None
        self._symbols_cache_time: float = 0.0
        self._last_request_time: float = 0.0
    
    def _throttle(self) -> None:
        """Throttle requests to respect Coinbase rate limits."""
        min_interval = 1.0 / self.MAX_REQUESTS_PER_SECOND
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.monotonic()
    
    def _get_retry_after(self, response: requests.Response) -> Optional[float]:
        """Parse Retry-After header if present."""
        retry_after = response.headers.get('Retry-After') if response is not None else None
        if retry_after is None:
            return None
        try:
            return float(retry_after)
        except (TypeError, ValueError):
            return None

    def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Execute an HTTP request with retries and exponential backoff."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self._throttle()
                response = self.session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 429:
                    raise requests.exceptions.HTTPError("Rate limit exceeded", response=response)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.MAX_RETRIES:
                    self.logger.error(f"Request failed after {attempt} attempts: {e}")
                    raise
                sleep_seconds = self.BACKOFF_FACTOR * (2 ** (attempt - 1))
                if isinstance(e, requests.exceptions.HTTPError) and getattr(e, 'response', None) is not None:
                    if e.response.status_code == 429:
                        retry_after = self._get_retry_after(e.response)
                        if retry_after is not None:
                            sleep_seconds = retry_after
                self.logger.warning(
                    f"Request attempt {attempt} failed for {url}: {e}; retrying in {sleep_seconds:.1f}s"
                )
                time.sleep(sleep_seconds)
        raise RuntimeError("Unexpected request retry failure")
    
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
                    'time': datetime.fromtimestamp(candle[0]).isoformat(),
                    'low': float(candle[1]),
                    'high': float(candle[2]),
                    'open': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            current_time = batch_end
        
        return candles
    

