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
# Lists Coinbase symbols only (the default exchange)
python main.py list-symbols

# Lists Binance symbols only; run separately from Coinbase
python main.py list-symbols --exchange binance
```

`list-symbols` reports one exchange per invocation. Run it once for each
exchange to see both lists; the Binance list uses Binance's native symbol
format.

Download data (default behavior: downloads all granularities if `--granularity` is omitted):

```bash
# Download Coinbase symbols from coinbase-download-symbols.txt
python main.py download --output ./data

# Download specific Coinbase symbols (single or multiple)
python main.py download --symbols BTC-USD ETH-EUR --output ./data

# Download only HOUR granularity for symbols in a file
python main.py download --symbols-file my-symbols.txt --granularity HOUR --output ./data

# Read the same BASE-QUOTE file on either exchange.
# For Binance, BTC-USDT is sent to the API as BTCUSDT.
python main.py download --exchange binance --symbols-file shared-symbols.txt --output ./data

# Read Binance symbols from binance-download-symbols.txt
python main.py download --exchange binance --output ./data
```

## Usage

See the CLI help for full options. Notable flags:

- `--exchange`: `coinbase` or `binance` (default: `coinbase`). Each command uses one exchange; `list-symbols` does not combine results.
- `--symbols`: One or more symbols (e.g., `BTC-USD ETH-EUR`).
- `--symbols-file`: Path to a symbols file. Defaults to `coinbase-download-symbols.txt` or `binance-download-symbols.txt` according to the selected exchange. An explicitly supplied file can be shared: use `BASE-QUOTE` notation (for example, `BTC-USDT`), which is converted to Binance's native `BTCUSDT` format when needed. Comma/semicolon-separated values and one symbol per line are supported; lines can contain comments starting with `#`.
- `--output`: Required. Directory where CSV/ZIP outputs will be saved.
- `--granularity`: `MINUTE`, `HOUR`, or `DAILY`. If omitted, the tool downloads data for all granularities.
- `--keep-csv`: Keep CSV files after compression (default: CSV files are deleted after zipping).

Date/time format for `--start-time` and `--end-time` is `yyyyMMdd-HH:MM:SS` (UTC).

### Exchange symbols and progress timestamps

Use `BASE-QUOTE` (such as `BTC-USD` or `BTC-USDT`) in symbols files for a common, shareable format. For Binance, the separator is removed before the symbol is sent to the API (`BTC-USDT` becomes `BTCUSDT`); no quote-currency remapping is performed, so `BTC-USD` becomes `BTCUSD`, not `BTCUSDT`. Existing Binance-native entries such as `BTCUSDT` remain accepted. Both exchanges still validate that every requested market is available on the selected exchange. `list-symbols` displays the selected exchange's own symbol format (Coinbase's hyphenated format or Binance's concatenated format).

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
- Symbols are normalized to uppercase. `BASE-QUOTE` entries work for either exchange; Binance's separator is removed before API requests. Existing concatenated Binance symbols are also accepted.

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
