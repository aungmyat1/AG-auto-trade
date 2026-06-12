# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-12

## Current Stage

**A2 built and gated (READ). Phase 6 nearly complete.** v4 build order position:

1. ✅ Validation core (gate, CPCV, purged WF, Monte Carlo, DSR, cost model) — 45 tests green
2. 🟡 Platform — risk engine + regime classifier implemented; **tests written 2026-06-12**;
   monitoring = Telegram stub; infrastructure/ + data/ empty
3. 🟡 Alpha modules — A2 ✅ READ verdict (2026-06-12); A1 spec locked (2026-06-12);
   A1 SMC detectors built (OB/FVG/BOS-CHOCH/Liquidity/Displacement, 2026-06-12);
   A1 AlphaModule wrapper + A3 ← **CURRENT GOAL**
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

## Known Gaps

| Gap | Action |
|---|---|
| ~~Branch protection OFF on `main`~~ | ✅ Closed 2026-06-12 |
| ~~No CI~~ | ✅ Closed 2026-06-12 |
| ~~Risk engine + regime classifier have zero tests~~ | ✅ Closed 2026-06-12 |
| ~~research_archive half-seeded~~ | ✅ Closed 2026-06-12 — M15, ALiVMassit, dual-mode verdict files added |
| Lock-before-look loader missing | Gate thresholds hardcoded in `gate.py`/`config.py`; no code reads GATE_DECISION.md. Build with alphas. |
| CPCV/WF train-side purge is a no-op | By design (no per-fold refit on a static trade series; test-side purge IS applied). Revisit if fold-wise fitting is added. |
| ~~`ag/validation/cost_models/` empty dup~~ | ✅ Closed 2026-06-12 |

## Next Goal

Build A1 AlphaModule wrapper (A1SmcMomentum class) that wires the 5 detectors +
regime/ATR pre-filters into propose() → SignalProposal per the locked spec.
Then A3 ensemble. Then race A1/A2/A3 through the identical gate on GC history.

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
