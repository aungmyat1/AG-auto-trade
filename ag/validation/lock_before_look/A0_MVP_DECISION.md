# PRE-REGISTERED GATE DECISION — A0_MVP
# Committed BEFORE any alpha sees data. Do NOT modify thresholds after data exposure.
# Locked: 2026-06-12

## Alpha Identity

**Alpha ID**: A0_MVP
**Description**: Phase B MVP — Sweep + ChoCH/BOS only (minimal filter set)
**Purpose**: Prove signal starvation is solved before layering additional filters.
  The "1-trade-per-363-pair-days" failure mode was caused by requiring all 10+
  conditions simultaneously. A0_MVP strips back to just two conditions.

**Relationship to A1**: A0_MVP is a SEPARATE alpha with its own gate run.
  It is NOT a modification of A1_SMC_MOMENTUM. If A0_MVP passes, its parameters
  are NOT retroactively applied to A1. A1 races the gate under its own spec.

## Signal Definition

A signal is generated when ALL of the following are true on a single bar:

1. **Sweep**: A liquidity sweep is detected on the lookback window
   (`SmcPipeline` with `PipelineConfig(sweep=True, choch=True, ob=False, fvg=False, displacement=False)`)
2. **ChoCH/BOS**: A structural break (Change of Character or Break of Structure)
   is detected after the sweep

No other filter is required for a signal. Specifically excluded from this alpha:
- Order block alignment
- Fair value gap presence
- Displacement candle
- Session window filter
- Volume filter
- HTF bias
- Kill zones
- Fibonacci levels

## Entry / Exit Model

- **Entry**: At close of the signal bar (next bar open acceptable for simulation)
- **Stop**: 0.5% below entry (long) / above entry (short) — corresponds to `stop_distance_pct=0.5`
- **Target**: 1.0% from entry — `target_distance_pct=1.0` → R:R = 2.0
- **Position size**: 0.5% of account per trade (G4 hard cap; non-negotiable)
- **Risk engine**: `RiskEngine.validate_entry()` called on every signal; no bypass

## Instruments and Data

- **Primary**: GC (CME Gold Futures) — same as A1 and A2
- **Secondary** (if n < 200 on GC alone): MGC; keep per-instrument models separate
- **Data source**: Databento OHLCV (1-minute bars, rolled to continuous contract)
- **Timeframe**: 1-hour bars (H1) for signal generation; 1-minute for entry simulation
- **IS/OOS split**: 70% in-sample / 30% out-of-sample (chronological, no look-ahead)
- **OOS period**: must be the most recent 30% of the data (walk-forward, not random)

## Cost Model

`CostModel.for_gc()` applied to ALL trade returns before gate scoring.
Net-of-cost PF is the only PF that counts. Gross PF is informational only.

## Acceptance Criterion Before Gate Run

**Signal rate floor**: The backtest must generate ≥ 1 entry per 20 bars on the IS data
before any quality assessment. If signal rate < 1/20 bars, re-run with lower
`swing_lookback` (try 3 → 2) and re-measure. Do NOT run the gate on fewer than 100 total trades.

## Gate Thresholds

IDENTICAL to `GATE_DECISION.md` (no special treatment for A0_MVP):

| Dimension          | Floor (read) | ROBUST (capital required) |
|--------------------|-------------|---------------------------|
| Trades (n)         | >= 50        | >= 200                    |
| Profit factor      | > 1.0 gross  | > 1.25 NET of realistic cost |
| Win rate           | —            | > 45%                     |
| Sharpe             | —            | > 1.2                     |
| Max drawdown       | —            | < 15%                     |
| CPCV median PF     | —            | > 1.0                     |
| Purged WF folds    | —            | >= 60% with PF > 1        |
| MC 5th-pct PF      | —            | > 0.9                     |
| Deflated Sharpe    | —            | > 0                       |

## Trial Count (--n-trials)

- Base: 1 (this spec defines a single signal variant: sweep+choch only)
- Each additional parameter tuned (lookback window, stop %, target %) adds 1 trial
- Each filter added or removed after seeing IS data adds 1 trial
- Log ALL trials in `ag/validation/trial_log.py` before running

## Verdict Disposition

| Verdict | Action |
|---|---|
| ROBUST | A0_MVP cleared; proceed to add one filter at a time (each as a new alpha ID) |
| READ | More data needed; do not tune — extend data window or wait for more history |
| FRAGILE | Archive to `research_archive/a0_mvp/`; do NOT modify signal to "fix" it |

## Rules

1. This file must not be modified after the first gate run on GC data.
2. Adding any filter (OB, FVG, session, etc.) requires a new alpha ID and new decision file.
3. The gate is identical for A0_MVP, A1, A2, A3 — no special treatment.
4. If A0_MVP is FRAGILE, that means sweep+choch alone has no edge on GC H1.
   That is a valid and important result. Archive it.
