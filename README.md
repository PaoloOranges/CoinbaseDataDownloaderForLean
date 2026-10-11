# Coinbase and Binance Data Downloader for LEAN

Download historical quote (OHLC) data from Coinbase Exchange or Binance and format it for use with the QuantConnect LEAN backtesting engine. The CLI can list available symbols and download historical data into compressed CSV files organized by symbol and granularity. Coinbase remains the default exchange.

## Quickstart

Install dependencies:

```bash
pip install -r requirements.txt
```

Run help:

```bash
python main.py --help
```

List available symbols:

```bash
python main.py list-symbols
```

List Binance symbols:

```bash
python main.py list-symbols --exchange binance
```

Download data (default behavior: downloads all granularities if `--granularity` is omitted):

```bash
# Download Coinbase symbols from coinbase-download-symbols.txt
python main.py download --output ./data

# Download specific Coinbase symbols (single or multiple)
python main.py download --symbols BTC-USD ETH-EUR --output ./data

# Download only HOUR granularity for symbols in a file
python main.py download --symbols-file my-symbols.txt --granularity HOUR --output ./data

# Download Binance symbols (Binance symbols use the exchange's native format)
python main.py download --exchange binance --symbols BTCUSDT ETHUSDT --output ./data

# Read Binance symbols from binance-download-symbols.txt
python main.py download --exchange binance --output ./data
```

## Usage

See the CLI help for full options. Notable flags:

- `--exchange`: `coinbase` or `binance` (default: `coinbase`). Can be used with either `list-symbols` or `download`.
- `--symbols`: One or more symbols (e.g., `BTC-USD ETH-EUR`).
- `--symbols-file`: Path to a symbols file. Defaults to `coinbase-download-symbols.txt` or `binance-download-symbols.txt` according to the selected exchange. Supports comma/semicolon-separated values or one symbol per line. Lines can contain comments starting with `#`.
- `--output`: Required. Directory where CSV/ZIP outputs will be saved.
- `--granularity`: `MINUTE`, `HOUR`, or `DAILY`. If omitted, the tool downloads data for all granularities.
- `--keep-csv`: Keep CSV files after compression (default: CSV files are deleted after zipping).

Date/time format for `--start-time` and `--end-time` is `yyyyMMdd-HH:MM:SS` (UTC).

### Exchange symbols and progress timestamps

Coinbase symbols use the `BASE-QUOTE` format, such as `BTC-USD`. Binance symbols use the native concatenated format, such as `BTCUSDT`; symbols are passed to Binance without quote-currency remapping.

Each exchange keeps download progress in a separate file alongside the symbols file: `coinbase-download-last-timestamps.json` or `binance-download-last-timestamps.json`. When no symbols file is specified, these files are located in the current working directory.

## Installation

Install in-place for development:

```bash
pip install -e .
```

## Output Format & Folder Layout

The tool writes compressed ZIP files grouped by granularity and symbol. Minute data is placed in a symbol-specific subfolder; hour and daily ZIPs are placed directly in their granularity folder. Example structure:

```
data/
├── minute/
│   └── btcusd/
│       ├── 20240101_btcusd_minute_trade.csv.zip
│       └── 20240102_btcusd_minute_trade.csv.zip
├── hour/
│   └── btcusd_trade.zip
└── daily/
    └── btcusd_trade.zip
```

Minute granularity is saved per-day as individual ZIPs; hour/daily granularity is grouped per-symbol into a ZIP.

## Notes on Symbols File

- Supports CSV (comma/semicolon) or one symbol per line.
- Lines starting with `#` or inline comments after `#` are ignored.
- Symbols are normalized to uppercase and validated against the selected exchange's format (`BTC-USD` for Coinbase, `BTCUSDT` for Binance).

## Changes in this release

- `--granularity` is now optional; omitting it will download data for all available granularities (`MINUTE`, `HOUR`, `DAILY`).
- Symbol file parsing improved to accept CSV, newline-separated lists, and comments.
- Added Binance symbol discovery and historical candle downloads via the Binance public market-data API.
- Added exchange selection, separate default symbols files, and separate timestamp files for Coinbase and Binance.
- Coinbase remains the default, preserving existing command behavior.

## Developer Notes

See `coinbase_downloader/` package for the implementation:
- `coinbase_downloader/cli/main.py` — CLI entry point
- `coinbase_downloader/downloader/base.py` — shared downloader behavior
- `coinbase_downloader/downloader/coinbase_downloader.py` — Coinbase API client
- `coinbase_downloader/downloader/binance_downloader.py` — Binance API client
- `coinbase_downloader/handlers/data_handler.py` — CSV and ZIP handling
- `coinbase_downloader/utils/utils.py` — helpers and constants

## Tests

Run the test suite with:

```bash
pytest
```

## License

See the LICENSE file.
