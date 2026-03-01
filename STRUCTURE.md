# Project Structure Overview

## Coinbase Data Downloader for LEAN

This is a complete Python console application for downloading cryptocurrency trade and quote data from Coinbase for use with LEAN algorithmic trading engine.

### Directory Structure

```
CoinbaseDataDownloaderForLean/
├── main.py                      # Main entry point and CLI interface
│                               # - Argument parsing
│                               # - Command routing (list-symbols, download)
│                               # - Logging configuration
│
├── coinbase_downloader.py       # Coinbase API interaction module
│                               # - get_available_symbols()
│                               # - get_historical_data()
│                               # - _fetch_candles()
│                               # - _fetch_trades()
│
├── data_handler.py              # Data I/O operations
│                               # - save_trades_to_csv()
│                               # - save_quotes_to_csv()
│                               # - load_trades_from_csv()
│                               # - load_quotes_from_csv()
│
├── utils.py                     # Utility functions
│                               # - validate_datetime_format()
│                               # - validate_symbol_format()
│                               # - format_bytes()
│                               # - format_number()
│
├── example.py                   # Example usage script
│                               # - Demonstrates programmatic API usage
│
├── tests.py                     # Unit tests
│                               # - Test utility functions
│                               # - Test data handler
│
├── requirements.txt             # Python dependencies
│                               # - requests
│                               # - python-dateutil
│
├── setup.py                     # Setup script for virtual environment
│                               # - Creates venv and installs dependencies
│
├── config.example.py            # Configuration template
│                               # - API settings
│                               # - Feature flags
│                               # - Rate limiting options
│
├── README.md                    # Original project README
├── README_USAGE.md              # Comprehensive usage documentation
├── QUICKSTART.md                # Quick start guide
├── STRUCTURE.md                 # This file
│
├── data/                        # Output directory (created on first run)
│   ├── BTC-USD_trades_*.csv
│   ├── BTC-USD_quotes_*.csv
│   └── ...
│
└── .gitignore                   # Git ignore patterns


### File Descriptions

#### Main Application Files

**main.py** (270 lines)
- Entry point for the console application
- Defines command-line interface with argparse
- Commands:
  - `list-symbols`: Lists all available trading pairs
  - `download`: Downloads historical data for specified symbols
- Features:
  - Datetime format parsing (yyyyMMdd-hh:mm:ss)
  - Argument validation
  - Logging setup
  - User-friendly error messages

**coinbase_downloader.py** (240 lines)
- Core module for interacting with Coinbase REST API v3
- Main methods:
  - `get_available_symbols()`: Fetches all tradable pairs
  - `get_historical_data()`: Downloads trades and quotes for a symbol
  - `_fetch_candles()`: Fetches OHLC data (batch processing with rate limiting)
  - `_fetch_trades()`: Fetches recent trades from Coinbase
- Features:
  - Error handling and retry logic
  - Rate limiting (0.1s delay between requests)
  - Automatic timestamp conversion
  - Validates symbols before download

**data_handler.py** (150 lines)
- Module for handling CSV I/O operations
- Methods:
  - `save_trades_to_csv()`: Saves trade data with columns: symbol, trade_id, time, price, size, side
  - `save_quotes_to_csv()`: Saves OHLC data with columns: symbol, time, open, high, low, close, volume
  - `load_trades_from_csv()`: Loads previously saved trades
  - `load_quotes_from_csv()`: Loads previously saved quotes
- Features:
  - Proper encoding (UTF-8)
  - Type conversion for numeric fields
  - Directory creation
  - Comprehensive error handling

**utils.py** (90 lines)
- Utility functions for validation and formatting
- Functions:
  - `validate_datetime_format()`: Validates yyyyMMdd-hh:mm:ss format
  - `validate_symbol_format()`: Validates symbol format (e.g., BTC-USD)
  - `format_bytes()`: Converts bytes to KB/MB/GB
  - `format_number()`: Formats numbers with thousand separators
  - `get_date_range_description()`: Creates human-readable date range descriptions

#### Documentation Files

**README_USAGE.md**
- Comprehensive user guide
- Installation instructions
- Command examples
- API documentation
- Troubleshooting guide

**QUICKSTART.md**
- Quick reference guide
- Common commands
- Important notes and limitations

**config.example.py**
- Configuration template
- API settings
- Rate limiting options
- Feature flags
- Can be extended for custom configurations

#### Support Files

**example.py**
- Demonstrates programmatic usage of the modules
- Examples:
  - Listing symbols
  - Downloading data
  - Loading CSV files
- Useful as a reference for integration

**tests.py**
- Unit tests using Python unittest framework
- Tests for:
  - Utility functions
  - Data handler operations
- Run with: `python -m pytest tests.py -v`

**setup.py**
- Automated setup script
- Creates Python virtual environment
- Installs dependencies
- Verifies installation
- Cross-platform (Windows, Linux, macOS)

**requirements.txt**
- Python package dependencies:
  - requests: HTTP library for API calls
  - python-dateutil: Date/time utilities

### Data Flow

```
User Command
    ↓
main.py (parse arguments)
    ↓
├─→ list-symbols:
│       ↓
│   coinbase_downloader.get_available_symbols()
│       ↓
│   Display results
│
└─→ download:
        ↓
    Validate parameters
        ↓
    coinbase_downloader.get_historical_data()
        ↓
    ├─→ _fetch_candles()
    │       ↓
    │   API calls (batched)
    │       ↓
    │   Parse JSON
    │       ↓
    │   Return quote data
    │
    └─→ _fetch_trades()
            ↓
        API call
            ↓
        Parse JSON
            ↓
        Return trade data
        ↓
    data_handler.save_trades_to_csv()
    data_handler.save_quotes_to_csv()
        ↓
    CSV files in ./data/
```

### CSV Output Format

**Trades CSV**
```
symbol,trade_id,time,price,size,side
ETH-EUR,12345678,2024-01-01T10:30:45.123456Z,1850.50,0.5,buy
ETH-EUR,12345679,2024-01-01T10:30:46.654321Z,1850.75,1.2,sell
```

**Quotes CSV**
```
symbol,time,open,high,low,close,volume
ETH-EUR,2024-01-01T10:00:00Z,1840.25,1852.50,1839.00,1850.50,125.43
ETH-EUR,2024-01-01T10:01:00Z,1850.50,1851.75,1848.25,1850.00,98.75
```

### API Endpoints Used

- `GET /products` - List all trading pairs
- `GET /products/{id}` - Get product details
- `GET /products/{id}/candles` - Get OHLC data
- `GET /products/{id}/trades` - Get recent trades

### Key Features

✓ **Multi-symbol support** - Download multiple symbols in one command
✓ **Date/time filtering** - Specify exact start and end times
✓ **CSV export** - Automatic CSV file generation
✓ **Error handling** - Comprehensive error messages and logging
✓ **Rate limiting** - Respects Coinbase API limits
✓ **Batch processing** - Handles large date ranges with batched requests
✓ **Cross-platform** - Works on Windows, Linux, and macOS
✓ **Extensible** - Well-structured code for easy modifications

### Limitations

- **Trade data**: Public API only provides last 100 trades (use Advanced Trade API for complete history)
- **Rate limits**: 15 requests per second on public endpoints
- **Candle granularities**: Fixed to 60, 300, 900, 3600, 21600, 86400 seconds
- **Authentication**: Currently uses public endpoints only (no private data)

### Future Enhancements

Possible improvements:
- [ ] Advanced Trade API integration (authenticated)
- [ ] Support for additional data formats (JSON, Parquet)
- [ ] Database storage options (SQLite, PostgreSQL)
- [ ] Incremental updates (append to existing CSVs)
- [ ] Data validation and quality checks
- [ ] Performance optimizations
- [ ] Web UI for easier access
- [ ] Scheduling and automated downloads
- [ ] Data aggregation and preprocessing
