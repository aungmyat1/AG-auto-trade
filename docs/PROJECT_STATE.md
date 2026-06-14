# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-14 (A0_MVP FRAGILE verdict recorded — freeze sequence complete, A1 next)

## Current Stage

**Phase A complete. Phase B complete. A0_MVP verdict recorded. FREEZE LIFTED — A1 gate race is next.**
v4 build order position:

1. ✅ Validation core (gate, CPCV, purged WF, Monte Carlo, DSR, cost model) — 45 tests green
   - CPCV train-side purging: implemented (was cosmetically a no-op)
   - Lock-before-look consistency test: A4 added (`tests/unit/test_lock_before_look.py`)
     verifies gate.py ↔ config.py ↔ GATE_DECISION.md alignment on every CI run
   - **TRGS built** (2026-06-14, PR #16) — 498 → 540 tests green
     `ag/validation/edge_validator.py`: permutation test (10k shuffles), ≥10% outperformance threshold.
     `ag/validation/readiness.py` (`TRGSDecisionEngine`): 6-state ladder:
       NOT_READY → READY_FOR_BACKTEST → READY_FOR_PAPER → READY_FOR_SHADOW → READY_FOR_LIVE / BLOCKED.
     BLOCKED supersedes all tiers (look-ahead, replay failure). READY_FOR_LIVE requires
     `manual_override=True` — OWNER ONLY, never the agent.
     `ag/validation/lock_before_look/TRGS_THRESHOLDS.md`: shadow tier (n≥500, DD<10%),
     live tier (manual_override only) — pre-registered lock-before-look.
     34 new tests: `test_edge_validator.py`, `test_readiness.py`.

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
   - **Pipeline preflight + bug fixes** (2026-06-14, PR #14):
     Bug 1: backtest wrote ALL signals (approved + rejected) to gate CSV — now writes only
       risk-approved trades with column renamed r_multiple → pnl_r.
     Bug 2: `scripts/run_gate.py` lacked sys.path setup — now self-contained, no PYTHONPATH needed.
     Preflight verified: backtest → gate pipeline runs end-to-end on synthetic data.
     Repo audit (`docs/audits/REPO_AUDIT_2026-06-14.md`): PASS overall, 4 open WARNs (non-blocking).

3. 🟡 Alpha modules:
   - A2: READ verdict (2026-06-12) — 10/11 criteria, DSR fail z=−25.32
   - **A0_MVP**: FRAGILE verdict (2026-06-14) — 38 trades, below READ floor (n<50), gate skipped
     Pipeline smoke test complete. Archived: `research_archive/a0_mvp/VERDICT.md`
   - A1: spec locked, detectors built, A1SmcMomentum wrapper built (not yet gated) ← NEXT
   - **A3**: spec locked (`A3_ENSEMBLE_DECISION.md`) + skeleton built (not yet gated)
   - Trial registry built: `ag/validation/trial_log.py` — honest --n-trials accounting
   - Backtest harness built: `scripts/run_alpha_backtest.py`
4. 🟡 Gate race (identical gate, all alphas) — A0_MVP FRAGILE; A1 is next
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
- 2026-06-14 (PR #14): backtest+gate pipeline bugs fixed; preflight verified end-to-end —
  suite 498/498 green
- 2026-06-14 (PR #16): TRGS added — edge_validator + TRGSDecisionEngine + TRGS_THRESHOLDS.md —
  suite **540 passed, 17 skipped**
- 2026-06-14 (PR #18): Databento loader fix (`stype_in=continuous`) — 557/557 green (17 skips resolved)
  GC 1m downloaded: 31,284 bars 2022-01-03→2024-12-30 cached to `/home/aungp/data/cache/GC_1m.parquet`
  v5 Bybit roadmap parked: `research_archive/deferred/bybit_smc_v5_roadmap.md`
- 2026-06-14 (A0_MVP run): 38 approved trades, WR 47.4%, mean R −0.003
  FRAGILE (below READ floor n<50, gate skipped). Pipeline confirmed end-to-end.
  All 4 audit items confirmed closed (S1/S6/S8/S9 fixed in earlier PRs).
  Archived: `research_archive/a0_mvp/VERDICT.md`

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
| ~~Backtest CSV included rejected signals~~ | ✅ Closed 2026-06-14 (PR #14 preflight fix) |
| ~~run_gate.py missing sys.path — failed without PYTHONPATH~~ | ✅ Closed 2026-06-14 (PR #14) |
| ~~No TRGS / deployment readiness firewall~~ | ✅ Closed 2026-06-14 (PR #16) |
| ~~`DATABENTO_API_KEY` not set~~ | ✅ Closed 2026-06-14 (PR #18) — 31,284 GC bars cached |
| ~~[AUDIT S1] FRAGILE header missing from SMC detector files~~ | ✅ Closed — all detector files confirmed with FRAGILE headers |
| ~~[AUDIT S9] `_active_obs` list unbounded~~ | ✅ Closed — capped at 50 in `a1_alpha.py` |
| ~~[AUDIT S8] No `TRIALS.md` parameter ledger~~ | ✅ Closed — `ag/alpha/a1_smc_momentum/TRIALS.md` exists, A0_MVP trial logged |
| ~~[AUDIT S6] No look-ahead regression tests for SMC detectors~~ | ✅ Closed (PR #14) — `tests/unit/smc/test_no_lookahead.py` covers all 4 detectors |
| ~~pyarrow not installed~~ | ✅ Closed 2026-06-14 (PR #18 install) |
| ~~ib_insync not installed~~ | ✅ Closed 2026-06-14 (PR #18 install) |
| No unit tests for cpcv/walk_forward/monte_carlo | Deferred post-verdict (Audit R7-R9) |
| CPCV/WF train-side purge scores only OOS | By design |

## Next Goal

**FREEZE LIFTED. Next: A1 gate race on GC 1h data.**

A0_MVP verdict recorded (FRAGILE, pipeline smoke test complete). All audit items closed.
Owner review of A0_MVP result is the gate before A1 begins.

  After owner review, the A1 sequence (~1–2 hours compute):

  1. Resample cached 1m to 1h:
     ```python
     import pandas as pd
     df = pd.read_parquet('/home/aungp/data/cache/GC_1m.parquet')
     df_1h = df.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
     df_1h.to_parquet('/home/aungp/data/cache/GC_1h.parquet')
     ```
  2. Log A1 baseline trial: `TrialRegistry().log("A1", "base: full WHERE filter sweep+choch+OB+FVG+displacement")`
  3. Run A1 backtest:
     `scripts/run_alpha_backtest.py --alpha a1 --data /home/aungp/data/cache/GC_1h.parquet --instrument GC --out results/a1_trades.csv`
  4. Run gate (only if n_approved ≥ 50):
     `scripts/run_gate.py results/a1_trades.csv --instrument GC --cost-preset gc --n-trials <count>`
  5. Record verdict: ROBUST/READ → here; FRAGILE → `research_archive/a1/VERDICT.md`
  6. Owner reviews → if ROBUST, A3 ensemble becomes buildable; if FRAGILE, reassess

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
