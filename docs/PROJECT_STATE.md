# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-12

## Current Stage

**A2 built and gated (READ). Phase 6 nearly complete.** v4 build order position:

1. ✅ Validation core (gate, CPCV, purged WF, Monte Carlo, DSR, cost model) — 45 tests green
2. 🟡 Platform — risk engine + regime classifier implemented; **tests written 2026-06-12**;
   monitoring = Telegram stub; infrastructure/ + data/ empty
3. 🟡 Alpha modules — A2 ✅ READ verdict (2026-06-12); A1 spec locked (2026-06-12);
   A1 SMC detectors built (OB/FVG/BOS-CHOCH/Liquidity/Displacement, 2026-06-12);
   A1SmcMomentum wrapper built (multi-OB tracking + full rejection logging, 2026-06-12);
   SmcPipeline composable architecture built; SignalFunnelTracker built;
   Phase 1 infra built (BacktestResult+4 metrics, CostModel.with_shock(),
   stress tests, synthetic scenarios — 209 tests green);
   scripts/run_signal_audit.py — progressive filter audit tool;
   A3 ← **CURRENT GOAL** (after Phase B MVP lock-before-look spec)
4. ⬜ Gate race (identical gate, all three alphas)
5. ⬜ Execution (Nautilus + IB) — forbidden until a ROBUST verdict exists

## Active Validation Target

- Instruments: GC (primary), MGC, 6E — per-instrument models, never shared
- Gate: `ag/validation/lock_before_look/GATE_DECISION.md` (locked 2026-06-12, immutable)
- Status of alphas: A1 SPEC LOCKED · A2 READ (OPTIMISTIC, n=325 OOS) · A3 NOT TESTED
  See `VALIDATION_STATUS.md` and `docs/validation/A2_GATE_RESULT.md`
- Live trading: **OFF** (no ROBUST verdict exists; nothing may trade)

## Last Validation Evidence

- 2026-06-12: A2 gated — 10/11 PASS, DSR FAIL (z=−25.32), verdict READ
  net PF=3.745, Sharpe=6.34, max DD=11.56%, CPCV=3.719, WF=100%, MC p5=3.745
- 2026-06-12: full test suite 45/45 green
- 2026-06-12: A1 SMC detectors built — OB, FVG, BOS/CHOCH, Liquidity, Displacement
  (ag/alpha/a1_smc_momentum/detectors/); SmcPipeline composable architecture built;
  SignalFunnelTracker (ag/validation/signal_audit/) built for Phase A audit;
  suite 173/173 green
- 2026-06-12: Phase 1 infra — BacktestResult +4 informational metrics (calmar_ratio,
  recovery_factor, max_consecutive_losses, time_in_drawdown_pct); CostModel.with_shock();
  A1SmcMomentum wrapper (ag/alpha/a1_smc_momentum/a1_alpha.py) with multi-OB tracking
  and per-filter rejection logging; stress test suite (36 new tests); synthetic scenarios;
  scripts/run_signal_audit.py progressive filter audit tool; suite 209/209 green

## Known Gaps

| Gap | Action |
|---|---|
| ~~Branch protection OFF on `main`~~ | ✅ Closed 2026-06-12 |
| ~~No CI~~ | ✅ Closed 2026-06-12 |
| ~~Risk engine + regime classifier have zero tests~~ | ✅ Closed 2026-06-12 |
| Risk G5 leverage guard is a no-op (`ag/risk/engine.py` — "enforced at execution layer"; pinned by `test_validate_entry_does_not_check_leverage`) | Implement `leverage` param + test before any execution work (`docs/IMPLEMENTATION_PLAN.md` Phase A item A2) |
| ~~research_archive half-seeded~~ | ✅ Closed 2026-06-12 — M15, ALiVMassit, dual-mode verdict files added |
| Lock-before-look loader missing | Gate thresholds hardcoded in `gate.py`/`config.py`; no code reads GATE_DECISION.md. Build with alphas. |
| CPCV/WF train-side purge is a no-op | By design (no per-fold refit on a static trade series; test-side purge IS applied). Revisit if fold-wise fitting is added. |
| ~~`ag/validation/cost_models/` empty dup~~ | ✅ Closed 2026-06-12 |

## Next Goal

Phase B MVP (Sweep+CHOCH only alpha):
  1. Write A0_MVP_DECISION.md (lock-before-look spec for Phase B MVP alpha).
     Do NOT run the gate on Phase B without this file committed first.
  2. Wire A1SmcMomentum(PipelineConfig(sweep=True, choch=True)) into a
     backtest loop; run scripts/run_signal_audit.py on real GC data.
  3. Measure funnel: sweeps → BOS/CHOCH → entries.  Target ≥1 entry per 20 bars.
     If trade count is still too low, lower swing_lookback (3→2) and re-measure.
  4. Once MVP produces ≥100 net trades, gate it. Then add one filter at a time.

After Phase B passes gate: A3 ensemble. Then race A0/A1/A2/A3 through identical gate.

Naming note: "Phase B" above is the dispatch phase name for the MVP alpha (A0).
`docs/IMPLEMENTATION_PLAN.md` Phase B = the Databento data layer — still unbuilt
(`ag/data/databento/` is an empty package) and a prerequisite for step 2's
real-GC-data signal audit and for any A1 gate run.

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
