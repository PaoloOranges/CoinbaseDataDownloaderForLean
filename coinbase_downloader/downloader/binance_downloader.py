"""Binance downloader implementation."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from coinbase_downloader.downloader.base import BaseDownloader


class BinanceDownloader(BaseDownloader):
    """Fetch historical OHLC data from the Binance REST API."""

    BASE_URL = "https://api.binance.com"
    MAX_CANDLES_PER_REQUEST = 1000
    MAX_REQUESTS_PER_SECOND = 10

    @property
    def default_symbols_file(self) -> str:
        return 'binance-download-symbols.txt'

    @property
    def timestamps_filename(self) -> str:
        return 'binance-download-last-timestamps.json'

    @property
    def granularity_map(self) -> Dict[str, int]:
        return {
            'MINUTE': 60,
            'HOUR': 3600,
            'DAILY': 86400,
        }

    def _interval_for_granularity(self, granularity_seconds: int) -> str:
        mapping = {
            60: '1m',
            300: '5m',
            900: '15m',
            3600: '1h',
            21600: '6h',
            86400: '1d',
        }
        if granularity_seconds not in mapping:
            raise ValueError(f"Unsupported Binance granularity: {granularity_seconds}")
        return mapping[granularity_seconds]

    def validate_symbol(self, symbol: str) -> bool:
        """Validate Binance symbol format and optionally verify against exchange metadata."""
        if not re.fullmatch(r'^[A-Z0-9]{5,}$', symbol or ''):
            return False
        try:
            return symbol in self.get_available_symbols()
        except requests.exceptions.RequestException:
            return True

    def get_available_symbols(self) -> List[str]:
        """Fetch all active trading pairs from Binance."""
        now = datetime.now(timezone.utc).timestamp()
        if self._symbols_cache and now - self._symbols_cache_time < self.CACHE_TTL_SECONDS:
            self.logger.debug('Returning cached Binance symbols')
            return self._symbols_cache

        try:
            self.logger.debug('Fetching available symbols from Binance...')
            response = self._request_with_retry('GET', f'{self.BASE_URL}/api/v3/exchangeInfo')
            payload = response.json()
            symbols = [
                item['symbol']
                for item in payload.get('symbols', [])
                if item.get('status') == 'TRADING'
            ]
            self._symbols_cache = sorted(symbols)
            self._symbols_cache_time = now
            self.logger.info(f'Found {len(self._symbols_cache)} available Binance symbols')
            return self._symbols_cache
        except requests.exceptions.RequestException as exc:
            self.logger.error(f'Failed to fetch Binance symbols: {exc}')
            raise

    def get_historical_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        granularity: int = 60,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Download OHLC candles for a Binance symbol."""
        self.logger.info(f'Fetching historical data for {symbol} from {start_time} to {end_time}')
        if not self.validate_symbol(symbol):
            raise ValueError(f'Invalid Binance symbol: {symbol}')

        quotes = self._fetch_candles(symbol, start_time, end_time, granularity)
        self.logger.info(f'Fetched {len(quotes)} candles for {symbol}')
        max_timestamp = max((q['time'] for q in quotes), default=None) if quotes else None
        return quotes, max_timestamp

    def _fetch_candles(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        granularity: int,
    ) -> List[Dict[str, Any]]:
        """Fetch OHLC candle data from the Binance klines endpoint."""
        candles: List[Dict[str, Any]] = []
        interval = self._interval_for_granularity(granularity)
        batch_ms = self.MAX_CANDLES_PER_REQUEST * granularity * 1000
        current_start = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        while current_start < end_ms:
            batch_end = min(current_start + batch_ms, end_ms)
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': batch_end,
                'limit': self.MAX_CANDLES_PER_REQUEST,
            }
            self.logger.debug(
                f'Fetching Binance candles for {symbol}: {current_start} to {batch_end}'
            )
            response = self._request_with_retry('GET', f'{self.BASE_URL}/api/v3/klines', params=params)
            batch_candles = response.json()
            if not batch_candles:
                break

            for candle in batch_candles:
                candles.append({
                    'symbol': symbol,
                    'time': datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc).isoformat(),
                    'low': float(candle[3]),
                    'high': float(candle[2]),
                    'open': float(candle[1]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                })

            current_start = int(batch_candles[-1][0]) + (granularity * 1000)

        return candles
