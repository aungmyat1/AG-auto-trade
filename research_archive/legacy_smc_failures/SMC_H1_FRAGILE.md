# Research Archive — SMC H1 (Gate-1 PASS, PREP-2 FRAGILE)

**Closed:** 2026-06-11
**Status:** CONCLUDED NOT ROBUST — do not re-run robustness tests; do not build Phase 2 on this entry

## Summary

BTCUSD H1 SMC entry passed the pre-declared Gate-1 criterion (PF > 1 OOS, n=333) but
failed the subsequent robustness gate (PREP-2) with median CPCV PF < 1.0 and
Monte-Carlo 5th-pct PF < 0.9. The entry line is concluded NOT ROBUST.

The canonical conclusion document is:
`docs/validation/SMC_ENTRY_CONCLUSION.md` (on main, as of 2026-06-11 / PR #207).
The caveats and multiple-testing context are in:
`docs/validation/SMC_GATE1_DECISION.md` (PREP-1 section, 2026-06-12).

## Gate-1 result (Phase C, BTCUSD H1)

OOS artefact: `verify_btc_1h_oos.json` @ commit `0adeb56` on `feat/smc-phase1-eurusd`

| Metric | Value | Gate | Pass? |
|---|---|---|---|
| Trades (OOS) | 333 | — | — |
| Profit Factor | 1.137 | > 1.0 after fees | PASS |
| Sharpe (annualized) | +0.18 | > 0 | PASS |
| Sharpe (per-trade) | 0.0171 | — | — |
| t-statistic | 0.31 | ≈ 2.0 for significance | MARGINAL |

PASS was carried mechanically on the committed criterion. t-stat 0.31 is noise-level.

Cross-instrument scope:
- EURUSD H1 (equivalent 2017-2022 period): PF 0.893 FAIL
- XAUUSD H1 (equivalent 2017-2022 period): PF 0.698 FAIL (gate-swap diagnostic: 0.657)
- XAUUSD H4: PF 0.810 FAIL

The edge was BTCUSD-specific and marginal even there.

## PREP-2 robustness result

Gate: pre-declared in `docs/roadmap/PHASE2_READINESS.md` before any PREP-2 results existed.

| Leg | Computed | Threshold | Pass? |
|---|---|---|---|
| Median CPCV PF | **0.9157** (40% of folds > 1) | > 1.0 | **FAIL** |
| % purged-WF folds PF > 1 | 60.0% (3/5, worst 0.9123) | ≥ 60% | pass |
| Monte-Carlo 5th-pct PF | **0.8890** (5th-pct equity −31R) | > 0.9 | **FAIL** |
| Deflated Sharpe (trials=2) | +0.0009 IS / −0.0114 OOS | > 0 | split — immaterial |

FRAGILE — two legs fail outright. The thin OOS pass (PF 1.137) is consistent with
sample luck; the edge does not survive resampling.

## What this means for future agents

- The PREP-2 robustness tests have been run and the artefacts are committed. Do not
  re-run them; the answer is known.
- The cross-instrument question (EURUSD/XAUUSD H1/H4) is also answered (negative on
  equivalent same-period data). Do not re-run blind; see the table above.
- The Phase 2 adaptive-TP work on PR #200 (`4aa988c`) is parked and carries no
  authorization (TP optimization is not permitted to flatter a rejected entry).
- The harness (walk-forward tooling, CPCV, Monte Carlo in `app/backtesting/`) is
  freed for the next strategy hypothesis.

## H1 strategy scaffold (available for the next hypothesis)

The freqtrade H1 strategy files produced during this investigation are preserved in:
- `research/smc-freqtrade/strategies/SMCSniperH1Strategy.py` — structure-based SL,
  4h HTF bias, 1h LTF entry, `active_ob_bounds()` for per-trade stop sizing
- `research/smc-freqtrade/tests/test_smc_detectors.py` — 10 L1 unit tests
- `research/smc-freqtrade/config/smc-h1-config.json` — Bybit futures dry-run config

These can serve as a starting template for a future H1+ strategy investigation, but
they must NOT be treated as a validated starting point. The parameters and architecture
are unvalidated beyond the sanity probe (1 trade in a 365-day window with non-default params).

## Artefacts on feat/smc-phase1-eurusd (held, unmerged)

- `verify_btc_1h_oos.json` @ `0adeb56` — Phase C OOS backtest artefact
- `smc_phase1_btcusd_h1_binance.json` @ `fe9439d` — in-sample backtest artefact
- PREP-2 robustness artefacts — posted as a comment on PR #200

The branch `feat/smc-phase1-eurusd` (PR #200) is held and parked. It is NOT to be
merged without explicit owner re-authorization after the SMC line is re-opened.
