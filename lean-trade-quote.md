# Trades vs. Quotes — QuantConnect Lean Codebase Analysis

## Core Distinction

**Trades** = actual executed transactions (what happened in the market).
**Quotes** = live bid/ask price offerings (what was available to trade).

---

## 1. Two Meanings of "Trade"

| Concept | Type | File | Purpose |
|---|---|---|---|
| **TradeBar** (OHLCV) | `TradeBar : BaseData, IBaseDataBar` | `Common/Data/Market/TradeBar.cs` | Input market data — price bars with Open, High, Low, Close, Volume |
| **Trade** (Closed position) | `Trade` | `Common/Statistics/Trade.cs` | Output/statistics — record of a round-trip entry→exit |

The **Quotes** counterpart is `QuoteBar` at `Common/Data/Market/QuoteBar.cs`.

---

## 2. Data Structure Comparison

| Property | **TradeBar** | **QuoteBar** |
|---|---|---|
| OHLC | Single OHLC (executed prices) | **Two** OHLC bars: `Bid` + `Ask` |
| Volume | `Volume` (executed quantity) | `LastBidSize` / `LastAskSize` (offer sizes, **not** volume) |
| Value | `Close` | Midpoint of `(Bid + Ask) / 2` |
| Interface | `IBaseDataBar` (Open/High/Low/Close) | `IBaseDataBar` (same, computed from midpoints) |

### 2.1 Tick-Level Difference

| Attribute | **Trade Tick** | **Quote Tick** |
|---|---|---|
| `TickType` | `TickType.Trade` | `TickType.Quote` |
| Key fields | `LastPrice`, `Quantity` | `BidPrice`, `AskPrice`, `BidSize`, `AskSize` |
| Value | Last trade price | Midpoint |

Enum defined at `Common/Global.cs:528-544`:
```csharp
public enum TickType { Trade, Quote, OpenInterest }
```

---

## 3. Market Defaults — Which Data Type Is Default

| Asset Class | **Default Data Type** | Reason |
|---|---|---|
| Equities | **Trade** (`IsDefaultDataType=true`) | Exchange-reported trades available |
| Forex / CFD | **Quote** only | No centralized trade reporting; pricing comes from dealer quotes |
| Crypto | **Both** Trade + Quote | Exchange reports both trades and order book |
| Options / Futures | Both (depends on subscription) | |

---

## 4. Slice Access

```csharp
slice.Bars["AAPL"]       // TradeBar collection (TradeBars)
slice.QuoteBars["AAPL"]  // QuoteBar collection
```

---

## 5. How Indicators Use Them

| Indicator Base | Consumes | Examples |
|---|---|---|
| `TradeBarIndicator` | Only `TradeBar` | Volume Profile, Accumulation/Distribution, Market Profile |
| `BarIndicator` | Either (`IBaseDataBar`) | Candlestick patterns, simple OHLC indicators |

QuoteBar implements `IBaseDataBar` via midpoint OHLC, so `BarIndicator` works with both.

---

## 6. Fill & Slippage Models

- **Fill models** prefer Quote data when available (more accurate execution pricing)
- `VolumeShareSlippageModel` uses `QuoteBar.LastBidSize`/`LastAskSize` for volume estimates
- `Security.Price` prefers QuoteBar over TradeBar when both share the same `EndTime` (`SecurityCache.cs:220-230`)

---

## 7. Consolidation Path

```
Trade Tick  → TickTradeBarConsolidator  → TradeBar
Quote Tick  → TickQuoteBarConsolidator   → QuoteBar
```

---

## 8. Key Files Summary

| File | Purpose |
|---|---|
| `Common/Data/Market/TradeBar.cs` | OHLCV trade bar definition |
| `Common/Data/Market/QuoteBar.cs` | Bid/Ask OHLC quote bar definition |
| `Common/Data/Market/Tick.cs` | Tick-level data (both Trade and Quote) |
| `Common/Global.cs` | `TickType`, `MarketDataType` enums |
| `Common/Data/SubscriptionDataConfig.cs` | `TickType` subscription routing |
| `Common/Data/TimeSliceFactory.cs` | Merges trade/quote into `Slice` |
| `Common/Data/Slice.cs` | `Bars` and `QuoteBars` accessors |
| `Indicators/TradeBarIndicator.cs` | Base for trade-only indicators |
| `Indicators/BarIndicator.cs` | Base for quote-compatible indicators |
| `Common/Statistics/Trade.cs` | Closed position record (execution stats) |
| `Common/Data/Market/TradeBars.cs` | `DataDictionary<TradeBar>` |
| `Common/Data/Market/QuoteBars.cs` | `DataDictionary<QuoteBar>` |

### Key Architectural Insight

QuoteBar can be **collapsed** into a TradeBar via `QuoteBar.Collapse()` — creating a midpoint-based TradeBar for backward compatibility. This is how Forex/CFD strategies using legacy `OnData(TradeBars)` still work despite having only quote data.

---

# Volume in Backtesting vs Live Trading

## Backtesting

Volume from **TradeBar** is used only by `VolumeShareSlippageModel` (`Common/Orders/Slippage/VolumeShareSlippageModel.cs:54-66`).

Fill models get OHLC prices from either TradeBar or QuoteBar but **volume is never used for fill pricing** — the `Prices` class (`Common/Orders/Fills/Prices.cs`) has no volume field.

## Live Trading

Fill models are **bypassed entirely**. The brokerage reports real fills via `OrdersStatusChanged` events — no `FillModel.Fill()` is ever called. Volume/slippage models are irrelevant.

## QuoteBar Has No Volume

`SecurityCache.Volume` is set exclusively from `TradeBar.Volume` (`SecurityCache.cs:274`). QuoteBar has **no Volume property** — it only has `LastBidSize` and `LastAskSize`.

---

# Data File Formats

## TradeBar CSV

6 columns (Crypto/Equity with volume) or 5 columns (Forex/CFD without volume):

| Col | Field |
|---|---|
| 0 | Time (ms-since-midnight for sub-hourly, or `yyyyMMdd HH:mm` for Hour/Daily) |
| 1 | Open |
| 2 | High |
| 3 | Low |
| 4 | Close |
| 5 | Volume (omitted for Forex/CFD) |

## QuoteBar CSV

11 columns:

| Col | Field |
|---|---|
| 0 | Time |
| 1 | Bid Open |
| 2 | Bid High |
| 3 | Bid Low |
| 4 | Bid Close |
| 5 | Last Bid Size |
| 6 | Ask Open |
| 7 | Ask High |
| 8 | Ask Low |
| 9 | Ask Close |
| 10 | Last Ask Size |

Empty-string OHLC columns (not `"0"`) mean that side's bar is null.

## File Path Structure

```
Data/<securityType>/<market>/<resolution>/<ticker>.zip
```

Zip entry name: `{yyyymmdd}_{ticker}_{resolution}_{ticktype}.csv`

---

# Crypto — Which Data Type?

Crypto subscribes to **both** by default (`SubscriptionManager.DefaultDataTypes` returns `[TickType.Trade, TickType.Quote]`).

| Property | Crypto Behavior |
|---|---|
| **Default subscriptions** | **Two**: TradeBar (TickType.Trade) and QuoteBar (TickType.Quote) |
| **IsDefaultDataType** | Returns `true` for **both** TradeBar and QuoteBar |
| **Price source** | `Crypto.Price` prefers **TradeBar** (`Crypto.cs:128`) |
| **Volume source** | Only from **TradeBar** — QuoteBar has no Volume |
| **Tick default** | `TickType.Quote` (like Forex/Cfd) |
| **Data file** | 6-column CSV with volume |
| **SecurityCache** | Both types update price, but Volume comes exclusively from TradeBar |

Crypto receives dual streams: TradeBars for volume/pricing and QuoteBars for bid/ask depth.
