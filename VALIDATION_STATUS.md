# VALIDATION STATUS — AG Auto Trade

Last updated: 2026-06-12
Gate version: v4 (locked in `ag/validation/lock_before_look/GATE_DECISION.md`)

## Alpha Verdicts

| Alpha | Status      | Trades (n) | Net PF | Verdict | Notes |
|-------|------------|------------|--------|---------|-------|
| A1    | NOT TESTED | —          | —      | PENDING | SMC-filter + momentum/delta |
| A2    | NOT TESTED | —          | —      | PENDING | Master-trader copy (SignalStart, 4,437 trades) |
| A3    | NOT TESTED | —          | —      | PENDING | Ensemble (A1×0.4 + regime×0.3 + A2×0.3 > 0.75) |

## Gate Thresholds (pre-registered, immutable)

See: `ag/validation/lock_before_look/GATE_DECISION.md`

Floor (READ): n >= 50, gross PF > 1.0
ROBUST (capital): n >= 200, net PF > 1.25, win rate > 45%, Sharpe > 1.2, max DD < 15%,
  CPCV median PF > 1.0, WF pass rate >= 60%, MC 5th-pct PF > 0.9, Deflated Sharpe z > 0

## Archived Results (validated NEGATIVE — from old system)

| Strategy | Verdict | Key numbers | Record |
|----------|---------|-------------|--------|
| crypto-SMC 5m sniper | FAIL | gross-negative | `research_archive/legacy_smc_failures/SMC_5m_SNIPER_FAIL.md` |
| crypto-SMC H1 entry | FRAGILE | CPCV median PF 0.9157, MC 5th-pct 0.8890 | `research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md` |
| M15 fee-trap | FAIL | gross-negative across 3 instruments | — |
| ALiVMassit | FRAGILE | 82.7% WR / 0.14 PF (WR ≠ edge) | — |
| dual-mode scalper | REVERTED | scalpers could never fire | — |

## Rules (immutable)

1. All three alphas race through the **identical** gate — no primacy by assertion.
2. FRAGILE verdict → `research_archive/` with verdict header. Not discarded, never re-tested.
3. If none pass, that is a valid result. **Do not relax thresholds.**
4. Only a ROBUST alpha earns `LIVE_TRADING = True` (30-day dry-run first, then 1% capital).
5. GATE_DECISION.md must not be modified after any alpha has seen the validation dataset.
