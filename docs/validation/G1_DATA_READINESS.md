# G1 DATA READINESS VERDICT
# Dispatch 1 — Data & Engine Audit
# Date: 2026-06-12 | Status: BLOCKED

---

## VERDICT: BLOCKED

Insufficient history, no real centralized volume, no delta series, and the candidate
engine (innovative_backtest_engine.py from auto-trade-system archive) lacks the
trial-count-aware Deflated Sharpe required by the v4/v6 gate spec.
G1 cannot run until Dispatch 3a is completed.

---

## 1. Engine Audit — innovative_backtest_engine.py

Source: `auto-trade-system-2026-06-12.tar.gz` →
`home/aungp/auto-trade-system/app/backtesting/innovative_backtest_engine.py`
(1322 lines, last updated 2026-05-27)

### Gate stats computed

| Stat | Present | Notes |
|---|---|---|
| Purged walk-forward | PARTIAL | IS/OOS split with 5-day purge gap; measures Sharpe per window, NOT PF per fold |
| CPCV overfit probability | APPROXIMATE | Defined as fraction of windows where OOS Sharpe degrades >30% vs IS — NOT true N-choose-k combinatorial CV |
| Monte Carlo p5 | YES | Block bootstrap 10,000 sims; checks p5 return > 0 |
| Bayesian edge prob | YES | Beta conjugate P(WR > 50% | data) ≥ 90% threshold |
| Trial-count-aware Deflated Sharpe (DSR) | **MISSING** | `_check_gate()` has no DSR check. Bayesian is present; DSR with explicit n_trials is absent. **v4/v6 requires DSR > 0 with explicit trial count — FLAG** |

### Phase-0B gate thresholds (as coded in `BacktestConfig` / `_check_gate`)

| Check | Threshold |
|---|---|
| IS Sharpe | ≥ 1.5 |
| IS Win rate | ≥ 55% |
| IS Profit factor | ≥ 1.5 |
| IS Max drawdown | ≤ 15% |
| OOS Sharpe | ≥ 80% of IS Sharpe |
| OOS Win rate | ≥ 90% of IS Win rate |
| WF profitable windows | ≥ 80% (v4 gate uses 60% — DISCREPANCY) |
| CPCV overfit prob | ≤ 25% |
| MC p5 return | > 0 |
| Bayesian edge prob | ≥ 90% |
| Deflated Sharpe z | **NOT CHECKED** |

**Differences vs v4 GATE_DECISION.md:**
- WF threshold: old engine 80% vs v4 60%
- Old engine checks Sharpe per fold; v4 checks PF per fold
- Old engine's "CPCV" is a degradation proxy, not true combinatorial purged CV
- v4 has trial-count-aware DSR (Bailey & Lopez de Prado 2014, `ag/validation/deflated_sharpe.py`); old engine does not
- v4's new engine (ag/validation/) IS the correct framework — the old engine should be treated as legacy

### Note on v4 validation framework

The v4 repo has a proper validation stack at `ag/validation/`:
`gate.py` | `cpcv.py` | `deflated_sharpe.py` (trial-count-aware) | `monte_carlo.py` | `walk_forward.py`

The v4 gate is the authoritative gate. The old innovative_backtest_engine.py is NOT the
engine to use for FILTERED-SMC G1.

---

## 2. Data Source Audit

### Price data via OHLCVStore (old system)

The old engine reads from PostgreSQL `price_candles` table (migration 011,
`app/data/ohlcv_store.py`). That Postgres instance is **NOT RUNNING** — the old
auto-trade-system was archived as DANGEROUS (2026-05-28 audit) and the VPS database
is down (socket `/var/run/postgresql/.s.PGSQL.5432` not found).

### Available local data

| File | Rows | Date range | Instrument | Volume type |
|---|---|---|---|---|
| `/home/aungp/vectorbt_data/XAUUSDT_1m.csv` | 91,719 | 2026-03-25 → 2026-05-29 (~65 days) | XAUUSD Bybit perp | Bybit perp volume |
| `data/signalstart/*/xauusd_trades.csv` | varies | Trade-level only | XAUUSD (signals) | N/A |
| `data/master_traders/master_trader_trades.db` | unknown | Trade-level only | XAUUSD (signals) | N/A |

### Key data quality checks

| Check | Result |
|---|---|
| Row count + date range | 91,719 rows, 65 days — **FAR TOO SHORT for deep-history backtesting** |
| Synthetic flag | Not in CSV schema (this is Bybit perp, not the old DB's synthetic+native blend) |
| Real VOLUME column | Column exists; volume is non-degenerate (89,347/91,719 non-zero); BUT it is **Bybit perpetual swap volume** — NOT centralized CME real volume |
| Delta / bid-ask / order-flow series | **NONE PRESENT** — no delta series in any available data |

### Databento / CME wiring check

```
find /home/aungp/ag-auto-trade -name "*.py" | xargs grep -l "databento" → ag/data/databento/__init__.py (empty stub)
grep -ri "GC=F\|GC/MGC\|6E" ag/ → NO matches
grep -ri databento ag/ → stub only, no implementation
```

`ag/data/databento/__init__.py` is an **empty stub** — no loader, no auth, no data.
`ag/data/ib_live/__init__.py` is similarly an empty stub.

**Real-volume GC/MGC + 6E futures history: NOT PRESENT.**
Only synthetic/Bybit data is available; the old system also relied on Yahoo Finance GC=F
proxies spliced with Bybit perp (synthetic_flag=True for ~85% of bars).

---

## 3. Summary Check Table

| Check | Result |
|---|---|
| Deep history (≥2y OHLCV for GC/MGC or 6E) | **FAIL — only 65 days Bybit 1m** |
| Real centralized CME volume (not proxy) | **FAIL — Bybit perp volume only** |
| Delta / order-flow series | **FAIL — absent** |
| Trial-count-aware DSR in engine | **FAIL — absent in old engine; present in v4 ag/validation/** |
| Databento wiring | **FAIL — stub only** |

---

## 4. Implications for Dispatches 2 & 3

**Dispatch 2 (G0 Spec Lock):** Must set INSTRUMENT PIN = BLOCKED.
Delta-trigger and volume-filter must be marked NOT-TESTED (cannot be evaluated
without the data). Only volume-free filters are testable on current data.

**Dispatch 3:** → **3a applies.** Wire a deep-history, real-volume source before G1.
Databento (CME GC/MGC + 6E, real centralized volume + L2 delta optional) is the
recommended path. **Requires owner go-ahead and subscription — see Dispatch 3 report.**

**G1 prerequisite list (must all be satisfied before running G1):**
1. Real-volume GC/MGC or 6E data (≥2y, CME-sourced) wired into `ag/data/`
2. Delta / order-flow series if delta-imbalance trigger is to be tested (optional — can exclude and mark NOT-TESTED)
3. `ag/validation/` used as the engine (not old innovative_backtest_engine.py)
4. Trial-count-aware DSR explicitly included in gate call (`n_trials` from §2 of FILTERED_SMC_DECISION.md)
