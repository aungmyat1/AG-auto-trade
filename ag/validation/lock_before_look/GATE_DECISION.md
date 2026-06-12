# PRE-REGISTERED GATE DECISION
# Committed BEFORE any alpha sees data. Do NOT modify thresholds after data exposure.
# Locked: 2026-06-12

## Gate Thresholds (v4 intraday gate)

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
| Deflated Sharpe    | —            | > 0 (trial count = total conditions/thresholds tried) |

## Cost Model (must be applied before gate scoring)

- GC/MGC: CME commission + spread + slippage per instrument spec
- 6E:     CME commission + spread + slippage per instrument spec
- Net-of-cost PF is the only PF that counts for the ROBUST verdict

## Alpha Modules Under Test

- A1: SMC-filter + momentum/delta (SMC = WHERE filter; momentum = WHEN trigger)
- A2: Master-trader copy (SignalStart, survivorship- and slippage-honest)
- A3: Ensemble (0.4*smc + 0.3*regime + 0.3*master_trader > 0.75)

## Rules

1. All three alphas race through this IDENTICAL gate — no primacy by assertion.
2. FRAGILE verdict → research_archive/ (not discarded, never promoted).
3. If none pass, that is a valid result. Do not relax thresholds.
4. Only a ROBUST alpha earns LIVE_TRADING = True (30-day dry-run first).
5. This file must not be modified after any alpha has been exposed to the validation dataset.
