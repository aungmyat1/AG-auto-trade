# VALIDATION STATUS — AG Auto Trade

Last updated: 2026-06-12
Gate version: v4 (locked in `ag/validation/lock_before_look/GATE_DECISION.md`)

## Engine Standard

**Gate engine: `ag/validation/` stack ONLY.**
`ag/validation/gate.py` · `cpcv.py` · `walk_forward.py` · `monte_carlo.py` · `deflated_sharpe.py`

The old `innovative_backtest_engine.py` (from auto-trade-system archive) is legacy — it lacks
trial-count-aware DSR and uses a Sharpe-degradation proxy instead of true CPCV. It must not be
used for any A1/A2/A3 gate evaluation. See `docs/validation/G1_DATA_READINESS.md` §1 for detail.

## Alpha Verdicts

| Alpha  | Status     | Trades (n) | Net PF | Verdict | Notes |
|--------|------------|------------|--------|---------|-------|
| A0_MVP | TESTED     | 38         | —      | **FRAGILE** | Sweep+ChoCH plumbing check; 38<50 READ floor → gate skipped; do not tune. `research_archive/a0_mvp/VERDICT.md` |
| A1     | NOT TESTED | —          | —      | PENDING | SMC-filter + momentum/delta; spec locked `A1_SMC_MOMENTUM_DECISION.md` |
| A2     | TESTED     | 325 (OOS)  | 3.745  | **READ (OPTIMISTIC)** | Master-trader copy; DSR fails (z=−25.32); 10/11 pass. See `docs/validation/A2_GATE_RESULT.md` |
| A3     | NOT TESTED | —          | —      | PENDING | Ensemble (A1×0.4 + regime×0.3 + A2×0.3 > 0.75); spec locked + skeleton built `A3_ENSEMBLE_DECISION.md` |

## Gate Thresholds (pre-registered, immutable)

See: `ag/validation/lock_before_look/GATE_DECISION.md`

Floor (READ): n >= 50, gross PF > 1.0
ROBUST (capital): n >= 200, net PF > 1.25, win rate > 45%, Sharpe > 1.2, max DD < 15%,
  CPCV median PF > 1.0, WF pass rate >= 60%, MC 5th-pct PF > 0.9, Deflated Sharpe z > 0

## Archived Results (validated NEGATIVE — from old system)

| Strategy | Verdict | Key numbers | Record |
|----------|---------|-------------|--------|
| crypto-SMC 5m sniper | FAIL | gross-negative | `research_archive/legacy_smc_failures/SMC_5m_SNIPER_FAIL.md` |
| crypto-SMC H1 entry | FRAGILE | CPCV median PF 0.9157, MC 5th-pct 0.8890 | `research_archive/2026-06-12_crypto_smc_fragile/` (verdict.json) · `research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md` |
| M15 fee-trap | FAIL | gross-negative across 3 instruments | — |
| ALiVMassit | FRAGILE | 82.7% WR / 0.14 PF (WR ≠ edge) | — |
| dual-mode scalper | REVERTED | scalpers could never fire | — |
| GoldTrendFollowing v2 | FRAGILE | OOS honest intrabar: n=47, PF 1.017, Sharpe 0.235, WR 34% | `docs/validation/GOLDTF_REVALIDATION.md` |

## Rules (immutable)

1. All three alphas race through the **identical** gate — no primacy by assertion.
2. FRAGILE verdict → `research_archive/` with verdict header. Not discarded, never re-tested.
3. If none pass, that is a valid result. **Do not relax thresholds.**
4. Only a ROBUST alpha earns `LIVE_TRADING = True` (30-day dry-run first, then 1% capital).
5. GATE_DECISION.md must not be modified after any alpha has seen the validation dataset.
