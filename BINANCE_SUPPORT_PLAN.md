# Plan: Extend to Support Binance

## Goal

Add Binance as a second market-data source alongside Coinbase without breaking
existing Coinbase behavior, CLI, entry points, or tests.

## Current Architecture (Coinbase)

```
coinbase_downloader/
├── cli/main.py              # CLI entry: list-symbols, download
├── downloader/              # Exchange API client (Coinbase REST)
├── handlers/data_handler.py # CSV + ZIP output, LEAN format
└── utils/utils.py           # Symbol/date parsing, granularity map
```

Coupling points to exchange specifics:

- `cli/main.py:13,47,85` — hardcodes `CoinbaseDownloader`
- `data_handler.py:215,231` — hardcoded `coinbase-download-last-timestamps.json`
- `utils.py:90` — `validate_symbol_format` requires `BASE-QUOTE` with `-`
- `cli/main.py:214` — default symbols file `coinbase-download-symbols.txt`

## Key Binance API Differences

| Aspect | Coinbase | Binance |
|---|---|---|
| Base URL | `api.exchange.coinbase.com` | `api.binance.com` |
| Symbol format | `BTC-USD` | `BTCUSDT` (no dash, quote appended) |
| Klines endpoint | `/products/{id}/candles` | `/api/v3/klines` |
| Time params | ISO 8601 | epoch **milliseconds** |
| Max per request | 300 candles | 1000 candles |
| Response | `[time, low, high, open, close, vol]` | `[openTime, open, high, low, close, vol, closeTime, ...]` |
| Rate limit | 15 req/s | weight-based (1200/min) |
| Granularities | 60/300/900/3600/21600/86400 | `1m,5m,15m,1h,4h,1d` |

## Target Structure

```
coinbase_downloader/                  # package name kept for backward compat
├── downloader/
│   ├── base.py                       # NEW: BaseDownloader ABC + shared HTTP logic
│   ├── coinbase_downloader.py        # refactored to inherit BaseDownloader
│   └── binance_downloader.py         # NEW
├── cli/main.py                       # add --exchange {coinbase,binance}
├── handlers/data_handler.py          # parameterize timestamps filename
└── utils/utils.py                    # add validate_binance_symbol
```

## Implementation Steps

### 1. `downloader/base.py` — exchange-agnostic contract

- `BaseDownloader(ABC)` owns shared `_throttle`, `_get_retry_after`,
  `_request_with_retry` (moved out of Coinbase).
- Abstract: `get_available_symbols`, `get_historical_data`,
  `validate_symbol`, `normalize_symbol`, `timestamps_filename`,
  `granularity_map`, `default_symbols_file`.

### 2. `downloader/coinbase_downloader.py` — inherit base

- Keep `get_available_symbols`, `_fetch_candles`, parsing unchanged.
- Implement the new contract methods by delegating to `utils`.

### 3. `downloader/binance_downloader.py` — NEW

- `BASE_URL = https://api.binance.com`, `MAX_CANDLES_PER_REQUEST = 1000`.
- `get_available_symbols` via `/api/v3/exchangeInfo` (status `TRADING`).
- `_fetch_candles` via `/api/v3/klines`:
  - datetime → epoch ms
  - granularity seconds → interval string (`60→1m`, `3600→1h`, `86400→1d`)
  - map `[openTime, open, high, low, close, volume, ...]` → quote dict
  - paginate with `startTime`/`endTime` until `end`.

### 4. `utils/utils.py`

- Add `validate_binance_symbol` (regex `^[A-Z0-9]{5,}$`).
- Keep `normalize_symbol` (already strips `-`, works for `BTCUSDT`).

### 5. `handlers/data_handler.py`

- `load_timestamps` / `save_timestamps` accept `filename: str` param with the
  existing Coinbase filename as default (backward compatible).

### 6. `cli/main.py`

- Add global `--exchange {coinbase,binance}` default `coinbase`.
- Factory `get_downloader(exchange)`.
- Default symbols file chosen by downloader.
- Validation via `downloader.validate_symbol`.
- Timestamps filename via `downloader.timestamps_filename()`.

### 7. Config / packaging

- `config.example.py`: add `BINANCE_API_BASE_URL`.
- `setup.py`: add `binance-downloader` console script (keep `coinbase-downloader`).
- `requirements.txt`: no new deps (`requests` suffices).

### 8. Tests

- Add Binance fixtures mocking `exchangeInfo` and `klines`.
- Assert symbol normalization, ms conversion, pagination loop.

## Decisions (resolved)

1. **Package name**: keep `coinbase_downloader` to avoid churn.
2. **Quote currency**: do NOT remap `BTCUSDT`→`BTCUSD`; pass Binance symbols
   through verbatim. Document this.
3. **Granularities**: keep the 3 (`MINUTE`/`HOUR`/`DAILY`) mapping to
   `1m`/`1h`/`1d`.
4. **Auth**: public market data only, no API keys.