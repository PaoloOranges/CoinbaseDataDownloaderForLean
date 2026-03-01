# Developer Guide

## Overview

This guide is for developers who want to extend or modify the Coinbase Data Downloader.

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│        Command-Line Interface       │
│             (main.py)               │
├─────────────────────────────────────┤
│  Commands                           │
│  ├─ list-symbols                    │
│  └─ download                        │
├─────────────────────────────────────┤
│    Coinbase API Layer               │
│   (coinbase_downloader.py)          │
├─────────────────────────────────────┤
│    Data Handling Layer              │
│    (data_handler.py)                │
├─────────────────────────────────────┤
│    Utilities & Validation           │
│       (utils.py)                    │
├─────────────────────────────────────┤
│    External Dependencies            │
│    ├─ requests (HTTP)               │
│    └─ python-dateutil               │
└─────────────────────────────────────┘
```

## Code Organization

### main.py
- **Purpose**: CLI interface and command routing
- **Responsibilities**:
  - Argument parsing (argparse)
  - Command dispatch
  - Logging setup
  - User interaction

**Key Functions:**
- `parse_datetime()`: Converts string to datetime object
- `list_symbols()`: Handles list-symbols command
- `download_data()`: Handles download command
- `main()`: Entry point

### coinbase_downloader.py
- **Purpose**: Abstracts Coinbase REST API
- **Responsibilities**:
  - API communication
  - Data fetching and parsing
  - Symbol validation
  - Rate limiting
  - Error handling

**Key Classes:**
- `CoinbaseDownloader`: Main class with methods:
  - `get_available_symbols()`: Fetch all trading pairs
  - `get_historical_data()`: Main method to download trades and quotes
  - `_fetch_candles()`: Get OHLC data
  - `_fetch_trades()`: Get recent trades

**API Base URL:**
```
https://api.exchange.coinbase.com
```

### data_handler.py
- **Purpose**: Data persistence and I/O
- **Responsibilities**:
  - CSV reading/writing
  - Data formatting
  - File management

**Key Methods:**
- `save_trades_to_csv(trades, filepath)`
- `save_quotes_to_csv(quotes, filepath)`
- `load_trades_from_csv(filepath)`
- `load_quotes_from_csv(filepath)`

### utils.py
- **Purpose**: Shared utility functions
- **Responsibility**: Validation and formatting

## Adding New Features

### Feature 1: Add JSON Export Support

**File: data_handler.py**

```python
import json

def save_trades_to_json(self, trades: List[Dict[str, Any]], filepath: Path) -> None:
    """Save trade data to JSON file."""
    filepath = Path(filepath)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(trades, f, indent=2, default=str)
    
    self.logger.info(f"Saved {len(trades)} trades to {filepath}")


def load_trades_from_json(self, filepath: Path) -> List[Dict[str, Any]]:
    """Load trade data from JSON file."""
    filepath = Path(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    self.logger.info(f"Loaded {len(trades)} trades from {filepath}")
    return trades
```

**File: main.py**

Add argument to download command:
```python
download_parser.add_argument(
    '--format',
    choices=['csv', 'json'],
    default='csv',
    help='Output format (default: csv)'
)
```

Modify download_data function:
```python
if args.format == 'json':
    data_handler.save_trades_to_json(trades, trade_path)
    data_handler.save_quotes_to_json(quotes, quote_path)
else:
    data_handler.save_trades_to_csv(trades, trade_path)
    data_handler.save_quotes_to_csv(quotes, quote_path)
```

### Feature 2: Add Symbol Filtering/Search

**File: main.py**

Add new command:
```python
search_parser = subparsers.add_parser(
    'search-symbols',
    help='Search symbols by pattern'
)
search_parser.add_argument('pattern', help='Search pattern (e.g., BTC, USD)')

# In main():
elif args.command == 'search-symbols':
    search_symbols(args.pattern)
```

**Implementation:**
```python
def search_symbols(pattern: str) -> None:
    """Search for symbols matching pattern."""
    downloader = CoinbaseDownloader()
    all_symbols = downloader.get_available_symbols()
    
    pattern = pattern.upper()
    matching = [s for s in all_symbols if pattern in s]
    
    print(f"\nSymbols matching '{pattern}' ({len(matching)} found):\n")
    for symbol in sorted(matching):
        print(f"  {symbol}")
    print()
```

### Feature 3: Add Authenticated Advanced Trade API

**File: coinbase_downloader.py**

```python
class CoinbaseAdvancedDownloader:
    """Use authenticated Advanced Trade API for complete history."""
    
    BASE_URL = "https://api.coinbase.com/api/v1"
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize with API credentials."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        # Add auth headers...
    
    def get_complete_trade_history(self, product_id: str, **kwargs):
        """Fetch complete trade history using authenticated API."""
        # Implementation...
        pass
```

## Testing

### Running Tests

```bash
python -m pytest tests.py -v
python -m pytest tests.py::TestDataHandler -v
python -m pytest tests.py::TestDataHandler::test_save_and_load_trades -v
```

### Adding New Tests

**File: tests.py**

```python
import unittest

class TestCoinbaseDownloader(unittest.TestCase):
    """Test Coinbase downloader functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.downloader = CoinbaseDownloader()
    
    def test_get_available_symbols(self):
        """Test fetching available symbols."""
        symbols = self.downloader.get_available_symbols()
        
        self.assertIsInstance(symbols, list)
        self.assertTrue(len(symbols) > 0)
        self.assertIn('BTC-USD', symbols)
    
    def test_is_valid_symbol(self):
        """Test symbol validation."""
        self.assertTrue(self.downloader._is_valid_symbol('BTC-USD'))
        self.assertFalse(self.downloader._is_valid_symbol('INVALID-XXX'))


if __name__ == '__main__':
    unittest.main()
```

## Performance Optimization

### 1. Parallelize API Calls

Currently sequential. Can be optimized with concurrent.futures:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_historical_data_parallel(self, symbols: List[str], ...):
    """Download data for multiple symbols in parallel."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(self._fetch_for_symbol, symbol, ...): symbol
            for symbol in symbols
        }
        
        results = {}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                trades, quotes = future.result()
                results[symbol] = (trades, quotes)
            except Exception as e:
                self.logger.error(f"Failed for {symbol}: {e}")
        
        return results
```

### 2. Batch CSV Writes

Instead of writing individual rows, batch them:

```python
def save_trades_to_csv_batch(self, trades: List[Dict], filepath, batch_size=1000):
    """Save trades in batches for better performance."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=...)
        writer.writeheader()
        
        for i in range(0, len(trades), batch_size):
            batch = trades[i:i+batch_size]
            writer.writerows(batch)
```

### 3. Cache Symbol List

```python
class CoinbaseDownloader:
    def __init__(self):
        self._symbol_cache = None
        self._cache_time = None
    
    def get_available_symbols(self, use_cache=True):
        """Fetch symbols with optional caching."""
        if use_cache and self._symbol_cache and self._is_cache_valid():
            return self._symbol_cache
        
        # Fetch from API...
        self._symbol_cache = symbols
        self._cache_time = datetime.now()
        return symbols
```

## Code Style Guidelines

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private methods: `_leading_underscore`

### Docstring Format

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description.
    
    Longer description if needed, explaining the function's purpose
    and behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: If something is wrong
    """
    pass
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import List, Dict, Any, Optional, Tuple

def fetch_data(
    symbol: str,
    start_time: datetime,
    end_time: datetime
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fetch trade and quote data."""
    pass
```

## Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Debug Output

```python
logger = logging.getLogger(__name__)
logger.debug(f"Processing {len(trades)} trades")
```

### Print Statements (Temporary)

```python
# For debugging only - remove before committing
import pprint
pprint.pprint(data)
```

## Common Tasks

### Update Dependencies

```bash
pip install --upgrade requests python-dateutil
pip freeze > requirements.txt
```

### Build Distribution

```bash
python -m build
twine upload dist/*
```

### Run Linter

```bash
pip install pylint
pylint main.py coinbase_downloader.py data_handler.py utils.py
```

### Format Code

```bash
pip install black
black main.py coinbase_downloader.py data_handler.py utils.py
```

## Git Workflow

### Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### Commit Changes

```bash
git add .
git commit -m "Add feature: description"
```

### Push and Create PR

```bash
git push origin feature/my-feature
```

## Extending the CLI

### Add New Subcommand

**File: main.py**

```python
# In main():
parser.add_subparsers(dest='command', ...)

# Add new subparser
export_parser = subparsers.add_parser('export', help='Export data')
export_parser.add_argument('input', help='Input CSV file')
export_parser.add_argument('--output-format', choices=['json', 'parquet'])

# In main():
elif args.command == 'export':
    export_data(args.input, args.output_format)
```

## Documentation

### Updating README

- Keep QUICKSTART.md for quick reference
- Keep README_USAGE.md for comprehensive guide
- Keep STRUCTURE.md for architecture overview

### Inline Documentation

```python
# Use docstrings for classes and functions
# Use comments for complex logic
# Use logging for runtime information
```

## Release Checklist

- [ ] Update version number
- [ ] Update CHANGELOG.md
- [ ] Run tests: `pytest tests.py -v`
- [ ] Run linter: `pylint *.py`
- [ ] Update documentation
- [ ] Update requirements.txt
- [ ] Tag release: `git tag v1.0.0`
- [ ] Push to repository

## Support

For questions or issues:
1. Check existing documentation
2. Review example.py
3. Enable verbose logging: `-v` flag
4. Check API status: https://status.coinbase.com/
