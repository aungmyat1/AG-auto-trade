# Validation Report Template

Fill this after every major backtest run before gate submission.
One file per alpha per run: e.g. `docs/validation/A1_GC_2026-07-01.md`

---

## RECONCILIATION NOTE (2026-06-12)

The gate thresholds in Section 3 (Sharpe ≥ 1.8, Max DD ≤ 12%, PF ≥ 1.6) are
Gate v2 drafts from VALIDATION_GATE_SPEC.md. They are NOT the current locked
thresholds. The locked gate (GATE_DECISION.md) uses:

  Sharpe > 1.2  |  Max DD < 15%  |  Net PF > 1.25

Do not submit a report using these stricter thresholds against the locked gate —
you will get false FAILs.  Use the actual thresholds from gate.py:
  ValidationGate.ROBUST_SHARPE = 1.2
  ValidationGate.ROBUST_MAX_DD = 0.15
  ValidationGate.ROBUST_PF_NET = 1.25

To use the stricter thresholds, write a new GATE_V2_DECISION.md lock file
and commit it BEFORE any alpha sees data.

---

## Validation Report

**Strategy Name**: `a1_smc_momentum`
**Report Date**: YYYY-MM-DD
**Version**: v0.1
**Alpha ID**: A1 | A2 | A3 | A0_MVP (circle one)
**Instrument**: GC | MGC | 6E
**n_trials**: (count every parameter/threshold combo tried — must be honest)

---

### 1. Strategy Summary

Brief description of the strategy logic.

---

### 2. Backtest Configuration

| Field | Value |
|---|---|
| Instruments | |
| Timeframes | |
| IS period | |
| OOS period | |
| Cost Model | `CostModel.for_gc()` / `CostModel.for_6e()` |
| n_trials | |

---

### 3. Performance Metrics (use LOCKED thresholds)

| Metric | Value | Locked Threshold | Pass? |
|---|---|---|---|
| Total Trades (floor) | | ≥ 50 | |
| Gross PF (floor) | | > 1.0 | |
| Total Trades (robust) | | ≥ 200 | |
| Net PF | | > 1.25 | |
| Win Rate | | > 45% | |
| Sharpe (annualized) | | > 1.2 | |
| Max Drawdown | | < 15% | |
| CPCV median PF | | > 1.0 | |
| WF pass rate | | ≥ 60% | |
| MC 5th-pct PF | | > 0.9 | |
| DSR z-score | | > 0 | |

*Informational only (not gate criteria):*

| Metric | Value |
|---|---|
| Calmar Ratio | |
| Recovery Factor | |
| Max Consecutive Losses | |
| Time in Drawdown % | |

---

### 4. Signal Funnel (attach tracker.report() output)

```
=== Signal Funnel Report ===
  Bars processed:
  Liquidity sweeps:
  BOS events:
  CHOCH events:
  ...
  Entries generated:
  Trades executed:

Bottleneck: [stage name]
```

---

### 5. Stress Test Results

| Test | Result | Notes |
|---|---|---|
| Walk-forward (5 folds) | | |
| CPCV (purged K-fold) | | |
| Cost shock (+50% spread, 2× slip) | | |
| Regime shift (trending→choppy) | | |
| Monte Carlo (10k, p5 PF) | | |

---

### 6. Verdict

**Gate verdict**: ROBUST / READ / FRAGILE

**Recommendation**: proceed / archive to research_archive/ / modify

**Notes**:
