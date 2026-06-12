# Research Archive — Crypto SMC (FRAGILE)

**Closed:** 2026-06-11
**Seeded:** 2026-06-12 (Phase 0 bootstrap of ag-auto-trade)
**Status:** CONCLUDED NOT ROBUST

This archive records the crypto SMC investigation that preceded the AG v3 plan.
It is preserved here as evidence that the validation pipeline works: a thin edge
was caught before capital deployment. See `verdict.json` for the numeric results.

## What was tested

BTCUSD H1 Smart Money Concepts strategy (Freqtrade + smartmoneyconcepts 0.0.27):
- HTF = 4h (bias + order blocks)
- LTF = 1h (sweep + ChoCH entry)
- Structure-based SL (sized to OB boundary, not fixed %)

Full research history lives in `smc-bot/` (standalone repo).

## Gate results (PREP-2, 2026-06-11)

| Check | Value | Threshold | Pass? |
|---|---|---|---|
| n (OOS trades) | 333 | — | — |
| Gross PF | 1.137 | > 1.0 | PASS (Gate-1) |
| Median CPCV PF | **0.9157** | > 1.0 | **FAIL** |
| % WF folds PF > 1 | 60% (3/5) | >= 60% | pass |
| MC 5th-pct PF | **0.8890** | > 0.9 | **FAIL** |
| Deflated Sharpe (trials=2) | +0.0009 IS / -0.0114 OOS | > 0 | split / immaterial |

FRAGILE: two legs fail outright. The thin OOS PASS (PF 1.137) is consistent
with sample luck; the edge does not survive resampling.

## What this means for AG v3

1. The robustness battery caught a thin edge before capital. This is the pipeline
   working exactly as designed — not a failure.

2. SMC is demoted to a **context filter** in AG v3 (A1 alpha: SMC says WHERE;
   momentum/delta says WHEN). It no longer holds entry-signal authority alone.

3. The CPCV + MC gate thresholds in `ag/validation/gate.py` are calibrated from
   this result: CPCV median > 1.0 and MC 5th-pct > 0.9 are the lines that would
   have caught this edge *before* Gate-1 if run prospectively.

4. The validation infra (CPCV, WF, MC, DSR) is now ported to `ag/validation/`
   as plain Python (no Freqtrade dependency) for use on futures data.

## Cross-instrument scope (also negative)

- EURUSD H1: PF 0.893 FAIL
- XAUUSD H1: PF 0.698 FAIL
- XAUUSD H4: PF 0.810 FAIL

The edge was BTCUSD-specific and marginal even there. Cross-instrument
universality is a requirement for AG v3 (GC + 6E models trained separately).
