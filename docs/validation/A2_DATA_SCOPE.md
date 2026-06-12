# A2 DATA SCOPE — MASTER TRADER COPY
# Dispatch 1 | Date: 2026-06-12
# READ-ONLY audit. No alpha code, no DB modifications.

---

## VERDICT: FUNDABLE-NOW

A2 (master-trader copy) can be built and gated with data already on disk.
No Databento, no CME futures, no paid data required.
Survivorship bias is present (moderate) and must be declared in the gate spec.

---

## 1. Source Location

**Primary DB**: `data/master_traders/master_traders/master_trader_trades.db`
(already in repo — no copy needed; treat as READ-ONLY research input)

**Raw CSVs** (import source): `data/signalstart/signalstart/<trader_id>/`
- `xauusd_trades.csv` — per-trader XAUUSD trade history
- `trade_history.csv` — some traders have this variant
- `trader_info.json` — metadata (name, stats at scrape time)

Schema: v2 SignalStart schema (NOT legacy Bybit copy-trading schema — that is blocked).

---

## 2. DB Profile

### Tables

| Table | Rows | Purpose |
|---|---|---|
| `trades` | 93,201 | All trade-level data — the primary research input |
| `masters` | 47 | Screened universe with computed metrics (from selector) |
| `traders` | 3 | Registry of traders imported via specific CSV paths |

### trades table fields

| Field | Type | Notes |
|---|---|---|
| trader_mark | TEXT | Trader ID (SignalStart UID) |
| symbol | TEXT | Instrument (XAUUSD and variants) |
| side | TEXT | BUY / SELL |
| open_time_ms | INTEGER | Entry timestamp, millisecond epoch |
| close_time_ms | INTEGER | Exit timestamp, millisecond epoch |
| open_time_dt | TEXT | ISO 8601 datetime string |
| close_time_dt | TEXT | ISO 8601 datetime string |
| entry_price | REAL | Master's entry price |
| exit_price | REAL | Master's exit price |
| size | REAL | Lot size (master's account units) |
| leverage | REAL | Leverage used |
| pnl | REAL | Master's reported gross PnL (USD, master's account scale) |
| pnl_pct | REAL | Master's reported PnL% |
| hold_hours | REAL | Duration in hours |
| session | TEXT | Session label (asian/london/ny/overlap/offhours) |
| raw_json | TEXT | Original SignalStart JSON payload |

### Null checks (no missing critical fields)

All of `entry_price`, `exit_price`, `pnl`, `open_time_ms`, `close_time_ms`, `size` = 0 nulls.

---

## 3. Universe Size & Date Range

**Total trades in DB**: 93,201 across 46 distinct trader_marks

**Per-trader trade counts and date ranges** (selected rows):

| trader_mark | n | First trade | Last trade | Notes |
|---|---|---|---|---|
| 272704 (SteadyRockGrowth) | 2,440 | 2021-12-09 | 2026-06-09 | Longest history (4.5y) |
| 275605 (MSC Gold Stable) | 1,500 | 2023-06-15 | 2026-06-03 | 3y track |
| 279689 (TradingBridgeGold) ★ | 525 | 2025-03-31 | 2026-06-04 | Selected — Tier A, PF 4.19 |
| 288043 (MSC Gold Legend) | 1,352 | 2024-11-19 | 2026-06-09 | Secondary Tier A |
| 263051 (TradeGoGold) | 163 | 2023-10-03 | 2024-04-02 | **Likely delisted** — data cuts off Apr-24 |
| 272637 (gold-ai-scalper) | 2,336 | 2024-04-25 | 2025-12-12 | **Likely delisted** — martingale, DD 312% |
| 275309 (Gold Lemonade) | 1,938 | 2024-10-11 | 2025-06-27 | **Possibly delisted** — cuts off Jun-25 |

★ = recommended selection per `selection_report.json`

**Instrument breakdown** (all gold):

| Symbol | n | Notes |
|---|---|---|
| XAUUSD | 57,455 | Most common (broker spot notation) |
| XAUUSDC | 27,985 | Alternative broker notation |
| XAUUSD.F | 2,792 | Another broker notation |
| Others | ~5,000 | GOLD#, XAUEUR, XAUUSD.S, etc. |

All instruments are spot gold (XAU/USD and equivalents). **No CME futures. No Databento required.**

---

## 4. Survivorship Check — MODERATE BIAS PRESENT

**Key question:** Does the DB hold only currently-listed (surviving) traders, or also delisted/blown ones?

**Answer: MIXED — recently-delisted traders ARE present; historically-delisted are NOT.**

Evidence:
- Traders with data cutoffs well before the scrape date (2026-06-09):
  - 263051 (TradeGoGold): last trade 2024-04-02 — listed for 177d then apparently delisted
  - 272637 (gold-ai-scalper): last trade 2025-12-12 — delisted, PF 0.74, DD 312%, martingale
  - 275309 (Gold Lemonade): last trade 2025-06-27 — possibly delisted
- These traders ARE in the DB with full trade history → they were collected before/at delisting

- Traders delisted BEFORE the scrape window began are NOT in the DB (we cannot observe them)
  - These are the "invisible" failures — traders who blew up in 2023 or earlier are absent
  - The DB represents traders that were active or recently active on SignalStart as of June 2026

**Implication: ANY gate verdict is OPTIMISTIC relative to the full historical universe.**

The selection_report.json explicitly flags martingale/blown traders as AVOID (263051, 272637,
288026, 287538 etc.) — so the selector does screen for blown accounts, but only within the
visible universe. Blowups that happened before the scrape remain invisible.

**Required handling in gate spec (Dispatch 2):**
- Label all A2 verdicts "OPTIMISTIC — survivor bias present"
- Bar does NOT lower for this; if anything, treat a ROBUST verdict with extra skepticism
- DO NOT use the blown/AVOID traders' data as IS training (263051, 272637 martingale)

---

## 5. Timestamp Granularity & Copy Latency

**Timestamp precision**: millisecond epoch stored in `open_time_ms` / `close_time_ms`.
However, actual time values are mostly minute-resolution — e.g., `17:15:00`, `15:30:00`, `09:45:00`.
Sub-minute precision is not reliably present in the source data (SignalStart publishes rounded times).

**Copy latency modelling**: 1-minute resolution means we CANNOT measure sub-minute
master→copy lag precisely. Must declare an assumption:

- Declared assumption (to be locked in Dispatch 2): **30-second copy lag** (master fill → copy fill)
  applied to every trade by adding 30s to `open_time_ms` for the copy entry, and using the
  price at that lagged time (or worst-case: `open_price + 0.5 × typical_spread` for slippage).
- Since data is 1-minute resolution, we cannot verify this assumption empirically.
  The 30s lag + spread slippage must be applied PESSIMISTICALLY.

**Slippage**: XAUUSD typical spread ~0.3–1.0 pips (broker-dependent). For the gate, use
conservative 0.5 pip per leg (= 0.005/oz = ~$0.50/oz) + 1 pip (broker commission round-trip).

---

## 6. PnL Field — Gross vs Net

The `pnl` field is the **master's reported gross PnL** scaled to the master's account size.
It is NOT directly usable for A2 sizing.

For A2, PnL is computed as:
```
a2_pnl = direction * (exit_price - entry_price - slippage) * a2_lot_size - commission
```
where `a2_lot_size` is derived from A2's own risk model (1% per trade on a reference account),
not from copying the master's dollar amount.

The master's `pnl` field is useful only for:
- Verifying trade direction is correctly signed
- Cross-checking R:R ratios for reasonableness

---

## 7. CME Futures / Databento Requirement

**None required for A2.** All trades are spot gold (XAUUSD and equivalents) from SignalStart.
The copy-trade validation uses the master's entry/exit prices as the signal; A2 executes against
its own forex broker (not CME). No real-volume futures data is needed.

This confirms Dispatch 0's HOLD decision: A2 can be built entirely from the on-disk DB.

---

## 8. Recommended Selected Master(s) (from selection_report.json)

The `selection_report.json` was produced by a MECHANICAL screener (survivability_score, PF, DD,
martingale flag, minimum trade count, minimum track length). This screener result IS the IS
selection rule for Dispatch 2 — provided its thresholds are explicitly documented.

| Rank | UID | Name | n | PF | WR | Max DD | Days | Tier | Rec |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 279689 | TradingBridgeGold | 525 | 4.19 | 77% | 4.4% | 430 | A | COPY |
| 2 | 288043 | MSC Gold Legend Pro | 1,352 | 3.88 | 81% | 5.3% | 567 | A | COPY |
| 3 | 275705 | MSC Gold Stable Pro | 897 | 3.16 | 82% | 5.5% | 777 | A | COPY |

Note: traders 279689 and 288043 together have 1,877 trades — above the ROBUST gate floor (n≥200).
But OOS trades (temporal split) will be fewer.

---

## 9. Data Verdict

| Check | Result |
|---|---|
| Trade-level data present | YES — 93,201 trades, 46 traders |
| Entry/exit price + timestamps | YES — all present, no nulls |
| Master's PnL direction | YES — usable for signal replay |
| Copy latency modellable | PARTIAL — 1-minute resolution; must declare 30s lag assumption |
| CME/Databento required | NO — pure SignalStart XAUUSD |
| Survivorship bias | MODERATE — recently-delisted visible; historically-delisted absent |
| Blown/martingale traders | PRESENT but flagged (AVOID) — must exclude from IS selection |
| ROBUST gate feasible | YES with OOS temporal split — see Dispatch 2 for OOS window |

**FUNDABLE-NOW**: proceed to Dispatch 2 (G0 spec) then Dispatch 3 (build + gate).
