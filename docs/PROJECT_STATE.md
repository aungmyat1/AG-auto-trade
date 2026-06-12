# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-12

## Current Stage

**Dispatch 4 complete. Phase A hardening done.** v4 build order position:

1. ✅ Validation core (gate, CPCV, purged WF, Monte Carlo, DSR, cost model) — 45 tests green
   - CPCV train-side purging: implemented (was cosmetically a no-op)
   - Lock-before-look consistency test: A4 added (`tests/unit/test_lock_before_look.py`)
     verifies gate.py ↔ config.py ↔ GATE_DECISION.md alignment on every CI run
2. ✅ Platform — risk engine + regime classifier + tests; monitoring = Telegram stub;
   infrastructure/ + data/ empty (Phase B)
   - G5 leverage guard: **FIXED** — now a real check (`validate_entry(leverage=1.0)`)
     previously a no-op comment; 5 new tests confirm enforcement
3. 🟡 Alpha modules:
   - A2: READ verdict (2026-06-12) — 10/11 criteria, DSR fail z=−25.32
   - A1: spec locked, detectors built, A1SmcMomentum wrapper built (not yet gated)
   - **A0_MVP**: spec locked (`A0_MVP_DECISION.md`) — sweep+choch only phase B MVP
   - **A3**: spec locked (`A3_ENSEMBLE_DECISION.md`) + skeleton built (not yet gated)
   - Trial registry built: `ag/validation/trial_log.py` — honest --n-trials accounting
   - Backtest harness built: `scripts/run_alpha_backtest.py`
4. ⬜ Gate race (identical gate, all alphas) — BLOCKED: Databento data
5. ⬜ Execution (Nautilus + IB) — forbidden until a ROBUST verdict exists

## Active Validation Target

- Instruments: GC (primary), MGC, 6E — per-instrument models, never shared
- Gate: `ag/validation/lock_before_look/GATE_DECISION.md` (locked 2026-06-12, immutable)
- Status of alphas:
  - A0_MVP: SPEC LOCKED · not yet gated
  - A1: SPEC LOCKED · not yet gated
  - A2: READ (OPTIMISTIC, n=325 OOS)
  - A3: SPEC LOCKED · skeleton built · not yet gated
- Live trading: **OFF** (no ROBUST verdict exists; nothing may trade)

## Last Validation Evidence

- 2026-06-12: A2 gated — 10/11 PASS, DSR FAIL (z=−25.32), verdict READ
  net PF=3.745, Sharpe=6.34, max DD=11.56%, CPCV=3.719, WF=100%, MC p5=3.745
- 2026-06-12: Phase 1 infra + A1 detectors — suite 209/209 green
- 2026-06-12 (Dispatch 4): G5 fix + A4 test + A0_MVP/A3 specs + trial registry
  + backtest harness — suite 253/253 green
- 2026-06-12 (test-plan reconciliation): monitoring tests (15) + offline E2E
  pipeline test (9: stub alpha → RiskEngine blocking verified → harness → gate;
  noise ≠ ROBUST safety check) — suite 304/304 green. Uploaded TEST_PLAN parked
  at `docs/reference/TEST_PLAN.md` with map; its §5.4 gate numbers superseded
  by locked GATE_DECISION.md

## Known Gaps

| Gap | Action |
|---|---|
| ~~Branch protection OFF on `main`~~ | ✅ Closed 2026-06-12 |
| ~~No CI~~ | ✅ Closed 2026-06-12 |
| ~~Risk engine + regime classifier have zero tests~~ | ✅ Closed 2026-06-12 |
| ~~research_archive half-seeded~~ | ✅ Closed 2026-06-12 |
| ~~G5 leverage guard was a no-op~~ | ✅ Closed 2026-06-12 (Dispatch 4) |
| ~~No lock-before-look consistency test~~ | ✅ Closed 2026-06-12 (Dispatch 4, A4) |
| ~~Trial registry missing~~ | ✅ Closed 2026-06-12 (Dispatch 4) |
| ~~A0_MVP spec not locked~~ | ✅ Closed 2026-06-12 (Dispatch 4) |
| ~~A3 spec not locked~~ | ✅ Closed 2026-06-12 (Dispatch 4) |
| Databento data layer | Phase B — BLOCKED on subscription |
| CPCV/WF train-side purge scores only OOS | By design (no per-fold refit on static series) |
| Lock-before-look loader missing | Gate thresholds hardcoded in gate.py; loader is the A4 test |

## Next Goal

Phase B — Data layer:
  1. Get Databento API key → `DATABENTO_API_KEY` in `.env`
  2. Build `ag/data/databento/loader.py` — OHLCV 1m+1h for GC/MGC/6E, parquet cache
  3. Build `ag/data/databento/integrity.py` — gap/duplicate/session checks
  4. Log A0_MVP trial in `trial_log.py`, run `scripts/run_alpha_backtest.py --alpha a0_mvp`
  5. Verify signal rate ≥ 1/20 bars. If not → lower swing_lookback, re-log trial.
  6. Gate A0_MVP: `scripts/run_gate.py trades.csv --instrument GC --n-trials <from log>`
  7. If A0_MVP ROBUST → add filters one at a time (each = new alpha ID + new decision file)

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
