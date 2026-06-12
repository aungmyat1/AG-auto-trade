# A2 MASTER TRADER GATE DECISION — G0 SPEC LOCK
# Committed BEFORE any gate run. Do NOT modify thresholds after any alpha has seen data.
# Changing any definition below = NEW TRIAL (increment n_trials in §4).
# Date locked: 2026-06-12

---

## §0 — SURVIVORSHIP DISCLOSURE

The SignalStart universe (93,201 trades, 46 traders as of 2026-06-09 scrape) contains
**recently-delisted traders** (data present) but NOT **historically-delisted traders**
(data absent — invisible failures from before the scrape window).

**ALL A2 verdicts are labeled OPTIMISTIC** — the gate is NOT relaxed for this; if anything,
a ROBUST verdict requires extra skepticism before deployment. The survivorship flag is
recorded on the verdict, not used to lower the bar.

---

## §1 — SELECTION RULE (mechanical, IS only)

The master(s) to copy are chosen by a **mechanical screener applied to the IS window only**.
Hindsight selection (picking by OOS performance, or by "what looked good in the full history")
is BANNED.

### Mandatory filters (must ALL pass to enter the candidate set)

| Filter | Threshold | Counted as DoF |
|---|---|---|
| Minimum trades (IS window) | ≥ 200 | 1 |
| Minimum track length | ≥ 365 calendar days | 1 |
| Martingale flag | must be False | 1 |
| Max drawdown (equity curve) | ≤ 20% | 1 |
| Profit factor (gross) | ≥ 1.5 | 1 |
| Win rate | ≥ 55% | 1 |

### Ranking metric

Candidates passing all filters are ranked by a composite score:
```
composite = 0.40 × norm(PF) + 0.30 × norm(1/max_dd) + 0.20 × norm(WR) + 0.10 × norm(days)
```
where `norm()` is min-max normalization across the candidate set.

The **top-1 ranked trader** is selected. If a basket (multi-trader) is tested, it counts as
a SEPARATE trial (+1 per additional basket composition tested — see §4).

### IS/OOS split

- **IS window**: all trades with `open_time_dt < IS_CUTOFF`
- **OOS window**: all trades with `open_time_dt >= IS_CUTOFF`
- `IS_CUTOFF` is set so that the selected trader has ≥ 200 IS trades AND ≥ 200 OOS trades
- The IS_CUTOFF is determined BEFORE looking at the OOS metrics
- For trader 279689 (TradingBridgeGold, first trade 2025-03-31, n=525):
  - Approximate IS_CUTOFF: 2025-11-01 (first ~200 trades IS, remaining ~325 OOS)
  - Exact cutoff must be computed as the timestamp of the 200th trade in sorted order
- IS_CUTOFF is a counted DoF only if multiple cutoffs are tried (+1 per cutoff tried)

### Exclusion list (applied before any gate run)

Traders flagged as AVOID in `selection_report.json` are excluded from the candidate set:
- 272637 (gold-ai-scalper): martingale, DD 312%, PF 0.74 — EXCLUDED
- 263051 (TradeGoGold): martingale, DD 111%, survivability 0.25 — EXCLUDED
- Any trader with martingale_flag=True in the DB — EXCLUDED

---

## §2 — EXECUTION-HONESTY MODEL (applied to EVERY copied trade)

### Copy latency
- **30-second lag** from master fill time → A2 fill time
- Applied by shifting `open_time_ms` + 30,000 ms for the copy entry
- At 1-minute timestamp resolution, entry price is adjusted by spread (see below)

### Slippage
- Entry slippage: **0.5 pip** per leg (= $0.50/oz) — conservative, applied to every trade
- This is pessimistic; actual may be lower but cannot be verified from 1-minute data

### Commission
- **1.0 pip round-trip** ($1.00/oz) = 0.5 pip per leg for broker commission
- Total per-trade cost: 1.0 pip entry (0.5 slip + 0.5 commission) + 0.5 pip exit (commission)
  = **1.5 pips total per trade** (~$1.50/oz round-trip)

### Position sizing
The master's PnL in USD is NOT copied directly (it is master-account-sized).
A2 uses its own sizing:
```
a2_lot_size = (account_equity × risk_per_trade) / (stop_loss_pips × pip_value)
```
- risk_per_trade: **0.5% of account equity** (same as A1 risk parameter — locked)
- stop_loss_pips: derived from `(entry_price - exit_price)` of the master's trade (proxy for the master's SL)
  If hold_hours < 0.5h AND the trade was a loss: use `abs(exit_price - entry_price)` as SL estimate
  If hold_hours ≥ 0.5h: use `1.0 × ATR(14)` on XAUUSD H1 at entry time as SL estimate (more conservative)
- For the gate run, use a fixed reference account equity of $10,000

### Net PnL formula
```
a2_trade_pnl = direction × (exit_price - entry_price) × a2_lot_size - total_cost
total_cost = 1.5 pips × pip_value × a2_lot_size
```

The master's reported `pnl` field is NOT used for A2 performance scoring.
Only the direction (BUY/SELL) and entry/exit prices are used.

---

## §3 — GENERATE_SIGNAL INTERFACE

A2 exposes: `generate_signal(context) -> BUY | SELL | NONE`

Signal generation rule (replay mode):
- At any timestamp T, check whether the selected master has an OPEN trade at T
- If master has an open trade with `open_time_dt <= T < close_time_dt`:
  - Return BUY if `side == 'BUY'`
  - Return SELL if `side == 'SELL'`
- Otherwise: return NONE

This is a **pure replay** — no look-ahead. The copy signal is only available AFTER the master's
trade is known to be open (i.e., after `open_time_dt + 30s lag`).

Copy open: at `open_time_dt + 30s`, at `entry_price + 0.5pip slip` (long) or `entry_price - 0.5pip slip` (short)
Copy close: at `close_time_dt`, at `exit_price - 0.5pip slip` (long) or `exit_price + 0.5pip slip` (short)

---

## §4 — TRIAL COUNT (frozen)

### Base degrees of freedom

| Parameter / threshold tested | Count |
|---|---|
| Min trades filter (200) | 1 |
| Min track length (365d) | 1 |
| Martingale filter | 1 |
| Max DD filter (20%) | 1 |
| PF filter (≥1.5) | 1 |
| WR filter (≥55%) | 1 |
| Composite score weights (fixed at 0.4/0.3/0.2/0.1) | 1 |
| IS/OOS split cutoff (200th trade) | 1 |
| Copy lag (30s) | 1 |
| Slippage assumption (0.5pip) | 1 |
| Commission (1.0pip RT) | 1 |

**Floor: 11**

### Rule
```
n_trials = max(configs_actually_evaluated, 11)
```

Any grid/sweep MULTIPLIES the count:
- Testing 3 different PF thresholds (1.2, 1.5, 1.8) = 3 trials for that parameter
- Testing top-1 vs top-3 basket = +2 trials
- Testing 2 different IS/OOS cutoffs = +1 additional trial

The REALIZED n_trials from the actual gate run must be logged in A2_GATE_RESULT.md.

---

## §5 — GATE CRITERIA (identical to A1/A3 — no special treatment for A2)

### LEVEL test (pre-registered thresholds — v4 gate, GATE_DECISION.md)

| Dimension | Floor (READ) | ROBUST |
|---|---|---|
| Trades (n OOS) | ≥ 50 | ≥ 200 |
| Profit factor (net of execution-honesty model) | > 1.0 gross | > 1.25 NET |
| Win rate | — | > 45% |
| Sharpe ratio | — | > 1.2 |
| Max drawdown | — | < 15% |
| CPCV median PF | — | > 1.0 |
| Purged WF folds PF > 1 | — | ≥ 60% |
| MC 5th-pct PF | — | > 0.9 |
| Deflated Sharpe z (trial-count-aware) | — | > 0 |

### MARGINAL test
A2 net-of-cost OOS PnL > naive equal-weight-all-traders OOS PnL on the SAME OOS window.
Both must be evaluated. (Naive baseline = hold XAUUSD long the entire OOS period, zero-cost.)

### Binding rule
Both LEVEL and MARGINAL must pass for ROBUST. Beating baseline alone is not sufficient.

### Survivorship note
ROBUST verdict is labeled **OPTIMISTIC** due to survivorship bias (§0).
It does not block deployment but must be documented in A2_GATE_RESULT.md.

---

## §6 — FRAGILE HANDLING

If FRAGILE:
- A2 drops to a context input for A3 ensemble (the `0.3 × master_trader` term)
- NOT discarded; NOT re-tuned to rescue it
- Archived in `research_archive/` with FRAGILE header
- The 0.3 A3 weight uses A2's signal as a regime-quality vote, not a direct entry

---

## §7 — AMENDMENT LOG (append only)

- 2026-06-12: Initial lock. Selected master = 279689 (TradingBridgeGold Forex Signals),
  Tier A, n=525, PF=4.19, DD=4.4%, WR=77%, 430 trading days. IS/OOS split at 200th trade.
  Trial floor = 11. Survivorship = MODERATE (recently-delisted visible; historically-delisted absent).
