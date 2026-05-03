# Coinbase Data Downloader for LEAN

Download historical trade and quote (OHLC) data from the Coinbase Exchange API and format it for use with the QuantConnect LEAN backtesting engine. This repository provides a small CLI to list available symbols and download historical data into compressed CSV files organized by symbol and granularity.

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

Download data (default behavior: downloads all granularities if `--granularity` is omitted):

```bash
# Download for symbols listed in the default file
python main.py download --output ./data

# Download specific symbols (single or multiple)
python main.py download --symbols BTC-USD ETH-EUR --output ./data

# Download only HOUR granularity for symbols in a file
python main.py download --symbols-file my-symbols.txt --granularity HOUR --output ./data
```

## Usage

See the CLI help for full options. Notable flags:

- `--symbols`: One or more symbols (e.g., `BTC-USD ETH-EUR`).
- `--symbols-file`: Path to a symbols file. Supports comma/semicolon-separated values or one symbol per line. Lines can contain comments starting with `#`.
- `--output`: Required. Directory where CSV/ZIP outputs will be saved.
- `--granularity`: `MINUTE`, `HOUR`, or `DAILY`. If omitted, the tool downloads data for all granularities.
- `--keep-csv`: Keep CSV files after compression (default: CSV files are deleted after zipping).

Date/time format for `--start-time` and `--end-time` is `yyyyMMdd-HH:MM:SS` (UTC).

## Installation

Install in-place for development:

```bash
pip install -e .
```

## Output Format & Folder Layout

The tool writes compressed ZIP files grouped by granularity and symbol. Example structure:

```
data/
├── minute/
│   └── btcusd/
│       ├── 20240101_btcusd_minute_trade.csv.zip
│       └── 20240102_btcusd_minute_trade.csv.zip
├── hour/
│   └── btcusd/
│       └── btcusd_trade.zip
└── daily/
	└── btcusd/
		└── btcusd_trade.zip
```

Minute granularities are saved per-day as individual ZIPs; hour/daily granularities are grouped per-symbol into a single ZIP per run.

## Notes on Symbols File

- Supports CSV (comma/semicolon) or one symbol per line.
- Lines starting with `#` or inline comments after `#` are ignored.
- Symbols are normalized to uppercase and validated against Coinbase format (e.g., `BTC-USD`).

## Changes in this release

- `--granularity` is now optional; omitting it will download data for all available granularities (`MINUTE`, `HOUR`, `DAILY`).
- Symbol file parsing improved to accept CSV, newline-separated lists, and comments.
- Output folders now include symbol subfolders for all granularities to avoid filename collisions.

## Developer Notes

See `coinbase_downloader/` package for the implementation:
- `coinbase_downloader/cli/main.py` — CLI entry point
- `coinbase_downloader/downloader/coinbase_downloader.py` — Coinbase API client
- `coinbase_downloader/handlers/data_handler.py` — CSV and ZIP handling
- `coinbase_downloader/utils/utils.py` — helpers and constants

## Tests

Run the test suite with:

```bash
pytest
```

## License

See the LICENSE file.
