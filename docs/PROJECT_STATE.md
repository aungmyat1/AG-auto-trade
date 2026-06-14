# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-14 (pre-gate audit: A1 spec ≠ code; A1_WHERE_ONLY lock spec created — PR #25 pending)

## Current Stage

**Phase A complete. Phase B complete. A0_MVP FRAGILE. Pre-gate audit found A1 spec not implemented.
A1_WHERE_ONLY locked as new alpha; gate run pending PR #25 merge.**
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
   - **A1 (full spec)**: spec locked (WHERE+WHEN, Z1–Z4, MT1–MT3) — **NOT BUILT**
     Pre-gate audit (2026-06-14) found A1SmcMomentum does not implement §1.
     §1 reserved for a fresh held-out data window. Not buildable on 2020-2024.
   - **A1_WHERE_ONLY**: built (sweep+ChoCH+OB+FVG+displacement, no WHEN gate)
     Lock spec created: `ag/validation/lock_before_look/A1_WHERE_ONLY_DECISION.md`
     n_trials=23 · IS cutoff=2022-12-30 · PR #25 pending merge
     Backtest results: GC 5yr 33 approved (WR 66.7%), 6E 5yr 3 (artifact)
     Gate run blocked until PR #25 merges. Expect FRAGILE.
   - **A3**: spec locked (`A3_ENSEMBLE_DECISION.md`) + skeleton built (not yet gated)
   - Trial registry built: `ag/validation/trial_log.py` — honest --n-trials accounting
   - Backtest harness built: `scripts/run_alpha_backtest.py`
4. 🟡 Gate race (identical gate, all alphas) — A0_MVP FRAGILE; A1_WHERE_ONLY pending
5. ⬜ Execution (Nautilus + IB) — forbidden until a ROBUST verdict exists

## Active Validation Target

- Instruments: GC (primary), 6E — per-instrument models, never shared (MGC deferred)
- Gate: `ag/validation/lock_before_look/GATE_DECISION.md` (locked 2026-06-12, immutable)
- Status of alphas:
  - A0_MVP: FRAGILE (archived 2026-06-14)
  - A1 (full spec): NOT BUILT — §1 WHERE+WHEN requires fresh data window
  - A1_WHERE_ONLY: LOCK PENDING (PR #25) · n_trials=23 · gate run next
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
- 2026-06-14 (PR #13): **LF-1 FIXED** — LiquidityDetector clusters past-only and dates the pool
  at the confirming swing (was: clustered with future equal-highs). 9/9 liquidity tests pass,
  still finds 9 pools, /smc-review PASS. **Replay-integrity suite** added
  (`ag/validation/replay_harness.py` + `tests/replay/`): ReplayHarness + future_leak_free /
  repaint_free — the future-poisoning check that CAUGHT LF-1. C3 tz test made portable.
  **v5 Bybit pivot REJECTED** on corrected facts — `research_archive/rejected_bybit_pivot_v5/`.
- 2026-06-14 (A0_MVP run): 38 approved trades, WR 47.4%, mean R −0.003
  FRAGILE (below READ floor n<50, gate skipped). Pipeline confirmed end-to-end.
  All 4 audit items confirmed closed (S1/S6/S8/S9). Archived: `research_archive/a0_mvp/VERDICT.md`
- 2026-06-14 (PR #22): A1 §9 per-instrument verdict-reading rule locked (before any gate run)
- 2026-06-14 (PR #23): ROADMAP synced to A1 backtest results (GC 33/6E 3 artifact)
- 2026-06-14 (pre-gate audit): A1SmcMomentum code does NOT implement §1 spec.
  Missing: MT1/MT2/MT3 WHEN trigger, Fib Z4, regime gate, ATR floor. 5 numeric params unlogged.
  Owner decision: Option C — new alpha ID A1_WHERE_ONLY, full §1 spec marked NOT BUILT.
- 2026-06-14 (PR #25): A1_WHERE_ONLY_DECISION.md locked (n_trials=23, IS=2022-12-30)
  A1_SMC_MOMENTUM_DECISION.md §8 amended (§1 NOT BUILT). 603/603 green. PR open.

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
| ~~[AUDIT S1] FRAGILE header missing from SMC detector files~~ | ✅ Closed 2026-06-14 (PR #13) — displacement header added; all other detectors already had it |
| ~~[AUDIT S9] `_active_obs` list unbounded~~ | ✅ Closed — capped at 50 in `a1_alpha.py:87-88` |
| ~~[AUDIT S8] No `TRIALS.md` parameter ledger~~ | ✅ Closed — `ag/alpha/a1_smc_momentum/TRIALS.md` exists, A0_MVP trial logged |
| ~~[AUDIT S6] No look-ahead regression tests for SMC detectors~~ | ✅ Closed 2026-06-14 (PR #13) — `tests/replay/` future-poisoning + repaint suite, all 5 detectors |
| ~~LF-1 LiquidityDetector future-cluster look-ahead~~ | ✅ Closed 2026-06-14 (PR #13) — past-only clustering; `future_leak_free` green; /smc-review PASS |
| ~~pyarrow not installed~~ | ✅ Closed 2026-06-14 (PR #18 install) |
| ~~ib_insync not installed~~ | ✅ Closed 2026-06-14 (PR #18 install) |
| No unit tests for cpcv/walk_forward/monte_carlo | Deferred post-verdict (Audit R7-R9) |
| CPCV/WF train-side purge scores only OOS | By design |
| A1 spec (§1 WHERE+WHEN) not implemented in built code | By design — gating A1_WHERE_ONLY separately; full-A1 needs fresh window |
| 6E stateful risk-engine artifact in multi-year backtests | 2020 COVID volatility locks engine for full run; per-year reset needed before 6E is gate-valid |
| MGC CostModel.for_mgc() not implemented | Deferred — needs CME/broker schedule verified; separate PR required |

## Next Goal

**Merge PR #25 → run A1_WHERE_ONLY gate → archive FRAGILE → A2 carries the race.**

  1. PR #25 merge on CI green (`lock/a1-where-only-spec`)
     Lock files: `A1_WHERE_ONLY_DECISION.md` + `A1_SMC_MOMENTUM_DECISION.md` §8 amendment

  2. Run A1_WHERE_ONLY per §9 (per-instrument, --n-trials 23):
     ```bash
     python3 scripts/run_alpha_backtest.py --alpha a1 \
         --data /home/aungp/data/cache/GC_1h.parquet \
         --instrument GC --cost-preset gc \
         --out results/a1_where_only_gc_trades.csv

     python3 scripts/run_alpha_backtest.py --alpha a1 \
         --data /home/aungp/data/cache/6E_1h.parquet \
         --instrument 6E --cost-preset 6e \
         --out results/a1_where_only_6e_trades.csv
     ```
     Gate only if OOS n ≥ 50; record verdict per §6 of A1_WHERE_ONLY_DECISION.md

  3. Record per-instrument verdicts in `research_archive/a1_where_only/VERDICT.md`
     Expect FRAGILE on both (GC 5yr ≈ 33 approved < READ floor 50)

  4. If FRAGILE: archive → A2 formal gate race begins
     A2 (READ n=325) runs through identical gate at honest --n-trials from trial_log.jsonl

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
