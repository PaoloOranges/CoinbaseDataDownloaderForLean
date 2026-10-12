"""Common downloader behavior shared across exchanges."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import requests


class BaseDownloader(ABC):
    """Exchange-agnostic HTTP and retry behavior for market data sources."""

    BASE_URL = ""
    MAX_CANDLES_PER_REQUEST = 300
    MAX_REQUESTS_PER_SECOND = 15
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.5
    CACHE_TTL_SECONDS = 300

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CoinbaseDataDownloader/1.0'
        })
        self._symbols_cache: Optional[List[str]] = None
        self._symbols_cache_time: float = 0.0
        self._last_request_time: float = 0.0

    @property
    def granularity_map(self) -> Dict[str, int]:
        return {
            'MINUTE': 60,
            'HOUR': 3600,
            'DAILY': 86400,
        }

    @property
    def default_symbols_file(self) -> str:
        return 'coinbase-download-symbols.txt'

    @property
    def timestamps_filename(self) -> str:
        return 'coinbase-download-last-timestamps.json'

    def _throttle(self) -> None:
        """Throttle requests to respect API rate limits."""
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
        headers: Optional[Dict[str, str]] = None,
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
                    timeout=10,
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

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Normalize symbol names for file and folder paths."""
        return symbol.lower().replace('-', '')

    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """Return all valid trading symbols for the exchange."""

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate a symbol string for this exchange."""

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_time,
        end_time,
        granularity: int = 60,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Download historical data for a symbol."""
