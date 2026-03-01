# Installation and Troubleshooting Guide

## Installation Methods

### Method 1: Automated Setup (Recommended)

The easiest way to set up the project:

```bash
cd CoinbaseDataDownloaderForLean
python setup.py
```

This script will:
1. Check your Python version
2. Create a virtual environment
3. Install all dependencies
4. Verify installation
5. Test the application

### Method 2: Manual Setup

#### 1. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Verify Installation

```bash
python main.py --help
```

### Method 3: No Virtual Environment (Not Recommended)

If you prefer to install globally:

```bash
pip install -r requirements.txt
python main.py --help
```

## First Time Usage

After installation:

### 1. List Available Symbols

```bash
python main.py list-symbols
```

This verifies that your installation works and shows you what symbols are available.

### 2. Download Sample Data

```bash
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240102-00:00:00
```

This downloads 1 day of data. Files will be saved to `./data/` directory.

### 3. Check Output

Navigate to the `data/` directory to verify the CSV files were created correctly.

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"

**Cause:** Dependencies not installed or virtual environment not activated

**Solution:**
```bash
# Make sure you're in the project directory
cd CoinbaseDataDownloaderForLean

# Activate virtual environment
# Windows: venv\Scripts\activate.bat
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### "Python 3.7 or higher is required"

**Cause:** Using an outdated Python version

**Solution:**
- Download Python 3.8+ from https://www.python.org/downloads/
- Verify installation: `python --version`
- Create new virtual environment with updated Python

### "Invalid datetime format" Error

**Cause:** Date/time format is incorrect

**Solution:**
- Use exactly this format: `yyyyMMdd-hh:mm:ss`
- Examples:
  - ✓ `20240101-09:30:00` (correct)
  - ✗ `2024-01-01 09:30:00` (wrong)
  - ✗ `01/01/2024 09:30` (wrong)

### "Invalid symbol" Error

**Cause:** Symbol doesn't exist or is incorrect

**Solution:**
```bash
# List available symbols
python main.py list-symbols

# Look for your symbol in the list and use exact name
# Examples: BTC-USD, ETH-EUR, XRP-GBP
```

### "Connection timeout" or Network Errors

**Cause:** Network connectivity issues or Coinbase API down

**Solution:**
1. Check your internet connection
2. Check if Coinbase API is online: https://status.coinbase.com/
3. Try again in a few minutes (rate limit may apply)
4. If using a proxy, configure your connection

### Empty CSV Files or "No data found"

**Cause:** Coinbase has limited historical data for trades

**Solution:**
- Trade data from public API is limited to last 100 trades
- Quote (OHLC) data is always available
- For complete history, consider:
  - Using authenticated Advanced Trade API
  - Using a different data source
  - Adjusting date range to recent data

### "Permission denied" on Linux/macOS

**Cause:** main.py not executable

**Solution:**
```bash
chmod +x main.py
chmod +x setup.py
```

### Script runs but produces incomplete output

**Cause:** API rate limiting or timeout

**Solution:**
1. The script automatically handles rate limiting
2. Try downloading a shorter date range
3. Use verbose mode to see progress: `python main.py -v download ...`

### Virtual Environment Issues

**"Cannot activate virtual environment"**

**Windows:**
- Try: `venv\Scripts\activate` (without .bat)
- Or use PowerShell: `venv\Scripts\Activate.ps1`

**Linux/macOS:**
- Try: `source venv/bin/activate`
- Check venv directory exists: `ls venv/`

**"Deactivate environment" (when done):**
```bash
deactivate
```

## Performance Tips

### Downloading Large Date Ranges

For large date ranges, the process may take a while:

1. **Use smaller chunks**: Download 7-30 days at a time
2. **Enable verbose mode**: `python main.py -v download ...` to see progress
3. **Multiple runs**: Run separate commands for different date ranges
4. **Background processing**: Run in a separate terminal so you can continue working

Example - Download one month in weekly chunks:
```bash
# Week 1
python main.py download BTC-USD --start 20240101-00:00:00 --end 20240108-00:00:00

# Week 2
python main.py download BTC-USD --start 20240108-00:00:00 --end 20240115-00:00:00

# Week 3
python main.py download BTC-USD --start 20240115-00:00:00 --end 20240122-00:00:00

# Week 4
python main.py download BTC-USD --start 20240122-00:00:00 --end 20240129-00:00:00
```

### Downloading Multiple Symbols

Downloading all symbols at once:
```bash
python main.py download BTC-USD ETH-USD XRP-USD SOL-USD --start 20240101-00:00:00 --end 20240107-23:59:59
```

## Getting Help

### Check Application Help

```bash
# General help
python main.py --help

# Command-specific help
python main.py download --help
```

### Enable Verbose Logging

```bash
python main.py -v download BTC-USD --start 20240101-00:00:00 --end 20240107-23:59:59
```

Verbose mode shows:
- API requests being made
- Data being parsed
- File operations
- Any warnings or errors

### Check CSV Files

After download, check one of the CSV files to verify format:

**On Windows (PowerShell):**
```powershell
Get-Content data/BTC-USD_trades_*.csv | Select-Object -First 5
```

**On Linux/macOS:**
```bash
head -5 data/BTC-USD_trades_*.csv
```

## System Requirements

- **Python**: 3.7 or higher
- **Memory**: 256 MB minimum
- **Disk Space**: Varies by data volume (typically 1-100 MB per month per symbol)
- **Internet**: Stable connection (API calls every ~0.1 seconds)
- **OS**: Windows, Linux, macOS

## Advanced Configuration

### Custom Configuration File

1. Copy `config.example.py` to `config.py`
2. Modify settings as needed
3. Import in your scripts: `from config import *`

### Programmatic Usage

See `example.py` for using the modules in your own code:

```python
from coinbase_downloader import CoinbaseDownloader
from data_handler import DataHandler
from datetime import datetime

downloader = CoinbaseDownloader()
handler = DataHandler()

# Get symbols
symbols = downloader.get_available_symbols()

# Download data
trades, quotes = downloader.get_historical_data(
    'BTC-USD',
    datetime(2024, 1, 1),
    datetime(2024, 1, 7)
)

# Save to CSV
handler.save_trades_to_csv(trades, 'trades.csv')
handler.save_quotes_to_csv(quotes, 'quotes.csv')
```

## Running Tests

```bash
# Run all tests
python -m pytest tests.py -v

# Run specific test class
python -m pytest tests.py::TestDataHandler -v

# Run specific test
python -m pytest tests.py::TestDataHandler::test_save_and_load_trades -v
```

## Uninstalling

To completely remove the project:

```bash
# Remove all output data
rmdir /s data     # Windows
rm -rf data       # Linux/macOS

# Remove virtual environment
rmdir /s venv     # Windows
rm -rf venv       # Linux/macOS

# Remove project directory if desired
```

## Support Resources

- **Coinbase API Docs**: https://docs.cdp.coinbase.com/exchange/reference
- **Python Requests Docs**: https://requests.readthedocs.io/
- **Python Official Docs**: https://docs.python.org/
- **LEAN Documentation**: https://www.quantconnect.com/docs

## Reporting Issues

When reporting issues, include:
1. Python version: `python --version`
2. Full error message (with verbose logging)
3. Command you ran
4. Operating system

Example:
```
Python 3.9.0
Windows 10
Error when running: python main.py download BTC-USD --start 20240101-00:00:00 --end 20240102-00:00:00
Error message: [full error text]
```
