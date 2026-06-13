# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-13 (Dispatch 6 — Phase B data layer: Databento + IB)

## Current Stage

**Dispatch 4 complete. Phase A hardening done.** v4 build order position:

1. ✅ Validation core (gate, CPCV, purged WF, Monte Carlo, DSR, cost model) — 45 tests green
   - CPCV train-side purging: implemented (was cosmetically a no-op)
   - Lock-before-look consistency test: A4 added (`tests/unit/test_lock_before_look.py`)
     verifies gate.py ↔ config.py ↔ GATE_DECISION.md alignment on every CI run
2. ✅ Platform — risk engine + regime classifier + tests; monitoring = Telegram stub;
   infrastructure/ + data/ populated (Phase B core built)
   - G5 leverage guard: **FIXED** — now a real check (`validate_entry(leverage=1.0)`)
     previously a no-op comment; 5 new tests confirm enforcement
   - **Test harness expanded** (Dispatch 5, 2026-06-12) — 259 → 392 tests green
     New coverage: `ag.risk.calculations` pure functions (position sizing, realized P&L,
     drawdown), circuit-breaker kill-switch patterns, SMC+RiskEngine integration,
     full trade-session lifecycle, A1 bar-by-bar backtest smoke test, e2e gate battery.
     New directories: `tests/unit/risk/`, `tests/integration/`, `tests/backtest/`,
     `tests/e2e/` — structure matches TEST_PLAN.md v1.0.
   - **Phase B data layer built** (Dispatch 6, 2026-06-13) — 392 → 498 tests green
     Databento path: `ag/data/databento/loader.py` offline-first; `integrity.py` 8-check
     OHLCV verifier; `tests/fixtures/synthetic.py` deterministic fixtures with defect injection.
     IB path: `ag/data/ib_live/historical.py` (`IBHistoricalLoader`) — same .load() API,
     CONTFUT continuous contract, chunked pacing, offline cache; `roll.py` CME expiry calendar
     + `get_front_month()`; `integrity.py` re-exports shared `check_ohlcv`.
     Source-agnostic factory: `ag/data/loader.py` → `get_loader("ib"|"databento")`.
     Tests: `test_loader.py`, `test_integrity.py`, `test_ib_loader.py`, `test_roll.py`
     (498 pass, 17 skip — parquet roundtrip and ib_insync tests skip when deps absent).
     `pyproject.toml`: `pyarrow>=15.0` in dev; `databento>=0.35` + `ib_insync>=0.9` in phase1.
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
- 2026-06-12 (Dispatch 5): test harness expansion — suite 392/392 green
  New: calculations unit tests, kill-switch tests, SMC+risk integration,
  risk backtest session, A1 smoke backtest, e2e gate battery
- 2026-06-13 (Dispatch 6): Phase B data layer — suite 498 passed, 17 skipped
  New: DatabentoLoader + IBHistoricalLoader (identical .load() API), check_ohlcv (shared),
  CME expiry/roll calendar, source-agnostic get_loader() factory, 99 new data tests;
  17 skips = parquet roundtrip + IB connection tests (need pyarrow/ib_insync/TWS)

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
| ~~calculations.py untested (position sizing, P&L, drawdown)~~ | ✅ Closed 2026-06-12 (Dispatch 5) |
| ~~No integration/backtest/e2e test directories~~ | ✅ Closed 2026-06-12 (Dispatch 5) |
| ~~Databento data layer (loader + integrity + fixtures)~~ | ✅ Closed 2026-06-13 (Dispatch 6) |
| ~~IB data layer missing~~ | ✅ Closed 2026-06-13 (Dispatch 6) |
| pyarrow not installed | `pip install -e ".[dev]"` unblocks 17 parquet/IB tests |
| ib_insync not installed | `pip install -e ".[phase1]"` needed for IB downloads |
| No IB account / TWS not configured | Set `IB_HOST/PORT` in `.env` (see `.env.ib.example`) |
| Databento API key not set | Add `DATABENTO_API_KEY` to `.env` to enable DB downloads |
| CPCV/WF train-side purge scores only OOS | By design (no per-fold refit on static series) |
| Lock-before-look loader missing | Gate thresholds hardcoded in gate.py; loader is the A4 test |

## Next Goal

Phase B — first download (IB path, cheapest + immediate):
  1. Install deps: `pip install -e ".[dev]" && pip install -e ".[phase1]"`
  2. Start TWS or IB Gateway (paper account fine). Copy `.env.ib.example` → `.env`, set port.
  3. Pull 6–12 months of GC + 6E 1h bars (one request each, fits within IB pacing):
     ```python
     from ag.data.loader import get_loader
     loader = get_loader("ib")
     df = loader.load("GC", "1h", start="2024-01-01", end="2024-12-31")
     ```
  4. Run integrity check: `from ag.data.ib_live import check_ohlcv; print(check_ohlcv(df,"GC","1h").summary())`
  5. Pull 1m bars for A0_MVP backtest (chunked — IB enforces 180D per request, loader handles pacing)
  6. Re-run tests — 17 skips should drop to 0 once pyarrow + ib_insync are installed
  7. Log A0_MVP trial in `trial_log.py`, run `scripts/run_alpha_backtest.py --alpha a0_mvp`
  8. Verify signal rate ≥ 1/20 bars. If not → lower swing_lookback, re-log trial.
  9. Gate A0_MVP: `scripts/run_gate.py trades.csv --instrument GC --n-trials <from log>`
  10. If A0_MVP ROBUST → add filters one at a time (each = new alpha ID + new decision file)

Databento upgrade path (when deeper history needed):
  - Add `DATABENTO_API_KEY` to `.env`; switch `get_loader("databento")`; same alpha code

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
