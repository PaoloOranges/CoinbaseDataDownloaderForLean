"""
Coinbase Data Downloader for LEAN
A Python package for downloading cryptocurrency trading data from Coinbase
"""

from coinbase_downloader.downloader import CoinbaseDownloader
from coinbase_downloader.handlers import DataHandler
from coinbase_downloader.utils import (
    GRANULARITY_SECONDS,
    format_bytes,
    format_number,
    get_date_range_description,
    normalize_symbol,
    parse_datetime,
    parse_iso_datetime,
    parse_symbols_file,
    validate_datetime_format,
    validate_symbol_format,
)

__version__ = "1.0.0"
__all__ = [
    'CoinbaseDownloader',
    'DataHandler',
    'GRANULARITY_SECONDS',
    'format_bytes',
    'format_number',
    'get_date_range_description',
    'normalize_symbol',
    'parse_datetime',
    'parse_iso_datetime',
    'parse_symbols_file',
    'validate_datetime_format',
    'validate_symbol_format',
]
