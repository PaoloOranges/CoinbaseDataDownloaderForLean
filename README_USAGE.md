# Coinbase Data Downloader for LEAN

A Python console application for downloading trade and quote data from Coinbase APIs. This tool allows you to download historical price data for cryptocurrency trading pairs and save them as CSV files for use with LEAN algorithmic trading engine or other analyses.

## Features

- **List available symbols**: Retrieve all tradable cryptocurrency pairs on Coinbase
- **Download trade data**: Get recent trades for specified symbols
- **Download quote data**: Get OHLC (Open, High, Low, Close) candle data with customizable granularity
- **Date/time filtering**: Specify exact date and time ranges for data download
- **Multi-symbol support**: Download data for multiple symbols in a single command
- **CSV export**: Automatically save data to CSV files with proper formatting
- **Comprehensive logging**: Detailed logging for monitoring and debugging

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### List All Available Symbols

To see all trading pairs available on Coinbase:

```bash
python main.py list-symbols
```

Example output:
```
Available Coinbase symbols (150+ total):

  BTC-EUR
  BTC-GBP
  BTC-USD
  ETH-EUR
  ETH-GBP
  ETH-USD
  ...
```

### Download Trade and Quote Data

#### Single Symbol

Download data for a single trading pair:

```bash
python main.py download ETH-EUR --start 20240101-00:00:00 --end 20240131-23:59:59
```

This saves data to the default `./data` directory:
- `ETH-EUR_trades_20240101_000000_to_20240131_235959.csv`
- `ETH-EUR_quotes_20240101_000000_to_20240131_235959.csv`

#### Multiple Symbols

Download data for multiple symbols at once:

```bash
python main.py download BTC-USD ETH-EUR XRP-USD --start 20240101-00:00:00 --end 20240131-23:59:59
```

#### Custom Output Directory

Specify a custom directory for saving CSV files:

```bash
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59 --output ./market_data
```

#### Verbose Logging

Enable detailed logging for debugging:

```bash
python main.py -v download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59
```

## Date/Time Format

All dates and times must use the format: **yyyyMMdd-hh:mm:ss**

Examples:
- `20240101-00:00:00` - January 1, 2024 at 00:00:00
- `20240615-14:30:45` - June 15, 2024 at 14:30:45
- `20241231-23:59:59` - December 31, 2024 at 23:59:59

## Output CSV Format

### Trades CSV

Columns: `symbol`, `trade_id`, `time`, `price`, `size`, `side`

```csv
symbol,trade_id,time,price,size,side
ETH-EUR,12345678,2024-01-01T10:30:45.123456Z,1850.50,0.5,buy
ETH-EUR,12345679,2024-01-01T10:30:46.654321Z,1850.75,1.2,sell
```

### Quotes (Candles) CSV

Columns: `symbol`, `time`, `open`, `high`, `low`, `close`, `volume`

```csv
symbol,time,open,high,low,close,volume
ETH-EUR,2024-01-01T10:00:00Z,1840.25,1852.50,1839.00,1850.50,125.43
ETH-EUR,2024-01-01T10:01:00Z,1850.50,1851.75,1848.25,1850.00,98.75
```

## API Information

This tool uses the **Coinbase REST API v3**:

- **Base URL**: https://api.exchange.coinbase.com
- **Rate Limit**: 15 requests per second (public endpoints)
- **Authentication**: Not required for public data endpoints
- **Documentation**: https://docs.cdp.coinbase.com/exchange/reference

### Data Limitations

- **Recent Trades**: The public API provides the last 100 trades only
- **Candle Data**: OHLC data is available with granularities of 60, 300, 900, 3600, 21600, or 86400 seconds
- **Historical Depth**: Candle data extends back indefinitely, but trade data is limited to recent trades

For complete historical trade data, consider using the Advanced Trade API with proper authentication.

## Examples

### Example 1: Download 1-minute candles for Bitcoin

```bash
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240102-00:00:00 --output ./btc_data
```

### Example 2: Download multiple altcoin pairs

```bash
python main.py download ETH-USD USDC-USD SOL-USD --start 20231201-00:00:00 --end 20231231-23:59:59 --output ./altcoins
```

### Example 3: Download with verbose logging to diagnose issues

```bash
python main.py -v download BTC-EUR --start 20240115-09:00:00 --end 20240115-17:00:00
```

## Error Handling

The application includes comprehensive error handling:

- **Invalid symbols**: Checked before download
- **Invalid date formats**: Detected and reported clearly
- **Network errors**: Logged with retry information
- **File I/O errors**: Caught and logged

All errors are logged to the console and can be reviewed with verbose logging enabled.

## Logging

Logs are displayed in the console with the following format:

```
2024-01-15 10:30:45,123 - root - INFO - Fetching available symbols...
2024-01-15 10:30:47,456 - coinbase_downloader - INFO - Found 150 available symbols
```

## Project Structure

```
CoinbaseDataDownloaderForLean/
├── main.py                      # Main entry point and CLI handler
├── coinbase_downloader.py       # Coinbase API interaction
├── data_handler.py              # CSV data I/O operations
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── data/                        # Default output directory (created on first run)
```

## Development

### Adding New Features

To extend the application:

1. **New API endpoints**: Add methods to `CoinbaseDownloader` class
2. **New data formats**: Add methods to `DataHandler` class
3. **New CLI commands**: Add subparsers to the argument parser in `main.py`

### Testing

You can test the application with:

```bash
# Test listing symbols (no data download)
python main.py list-symbols

# Test download with a small date range
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240101-01:00:00 --output ./test_data
```

## Troubleshooting

### "No data found" or empty CSV files

- Coinbase may not have recent trade data for older date ranges
- Try downloading recent data (within the last month)
- Verify the symbol exists using `list-symbols`

### Connection timeouts

- Check your internet connection
- Verify Coinbase API is accessible
- Try again after a few minutes (may be rate limited)

### Invalid date format errors

- Ensure dates follow exactly: `yyyyMMdd-hh:mm:ss`
- Check that start date is before end date
- Verify month (01-12) and day (01-31) are valid

## License

See LICENSE file for licensing information.

## Support

For issues or feature requests, please refer to the main project repository.

## References

- Coinbase API Documentation: https://docs.cdp.coinbase.com/exchange/reference
- LEAN Algorithmic Trading: https://www.quantconnect.com/lean
- Python requests library: https://requests.readthedocs.io/
