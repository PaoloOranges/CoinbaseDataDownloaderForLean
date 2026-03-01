# Quick Start Guide for Coinbase Data Downloader

## 1. Install Dependencies (First Time Only)

```bash
pip install -r requirements.txt
```

## 2. Verify Installation

```bash
python main.py --help
```

You should see the help message with available commands.

## 3. List Available Symbols

```bash
python main.py list-symbols
```

This will display all available trading pairs on Coinbase.

## 4. Download Data

### Example 1: Simple single symbol download
```bash
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59
```

### Example 2: Multiple symbols
```bash
python main.py download BTC-USD ETH-EUR XRP-USD --start 20240101-00:00:00 --end 20240131-23:59:59
```

### Example 3: Custom output location
```bash
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59 --output ./my_data
```

### Example 4: Verbose mode (for debugging)
```bash
python main.py -v download BTC-USD --start 20240101-00:00:00 --end 20240131-23:59:59
```

## 5. Understanding Output

Each download creates two CSV files:
- `SYMBOL_trades_TIMESTAMP.csv` - Individual trade records
- `SYMBOL_quotes_TIMESTAMP.csv` - OHLC candle data

## Important Notes

⚠️ **Date Format**: Always use `yyyyMMdd-hh:mm:ss` format
- Correct: `20240101-09:30:00`
- Wrong: `2024-01-01 09:30:00` or `01/01/2024 09:30:00`

⚠️ **Trade Data Limitation**: The Coinbase public API only provides the last 100 trades. For complete historical trade data, you would need the Advanced Trade API with authentication.

⚠️ **Rate Limiting**: The application automatically respects Coinbase's rate limits (15 requests/second), so downloads are manageable.

## Troubleshooting

### "Module not found" error
- Make sure you've installed requirements: `pip install -r requirements.txt`

### Empty CSV files
- Coinbase may not have historical trade data for the date range
- Quote (OHLC) data is always available for all symbols

### "Invalid symbol" error
- Run `python main.py list-symbols` to see available symbols
- Symbol names are case-sensitive and use formats like `BTC-USD`, `ETH-EUR`

## Next Steps

- Read the full [README_USAGE.md](README_USAGE.md) for detailed documentation
- Check [example.py](example.py) for programmatic usage examples
- Explore the module files for further customization
