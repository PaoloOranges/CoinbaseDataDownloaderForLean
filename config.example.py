# Configuration Example
# Copy this file to config.py to use custom configurations

# Coinbase API Configuration
COINBASE_API_BASE_URL = "https://api.exchange.coinbase.com"

# Rate limiting configuration
REQUEST_TIMEOUT_SECONDS = 30
RATE_LIMIT_DELAY = 0.1  # Delay between requests in seconds (Coinbase allows 15 req/sec)

# Candle granularity options (in seconds)
CANDLE_GRANULARITIES = {
    '1min': 60,
    '5min': 300,
    '15min': 900,
    '1hour': 3600,
    '6hour': 21600,
    '1day': 86400
}

# Default granularity (in seconds)
DEFAULT_GRANULARITY = 60  # 1 minute

# Data export configuration
EXPORT_FORMATS = ['csv']  # Add 'json', 'parquet', etc. in future
DEFAULT_EXPORT_FORMAT = 'csv'

# Logging configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = None  # Set to a path like 'coinbase_downloader.log' to enable file logging

# Output directory configuration
DEFAULT_OUTPUT_DIR = './data'
CREATE_SYMBOL_SUBDIRS = False  # Set to True to create subdirectories per symbol

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries

# Features
INCLUDE_TRADES = True   # Download recent trades
INCLUDE_QUOTES = True   # Download OHLC candles
