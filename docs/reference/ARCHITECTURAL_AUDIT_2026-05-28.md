# Architectural Audit — Auto Trade System

**Date:** 2026-05-28
**Auditor role:** senior quantitative trading systems architect / low-latency execution engineer
**Scope:** entire `app/` (66,859 LOC), Docker topology, observability, dashboards
**Verdict:** DANGEROUS for live capital
**Prerequisite for production:** Wave 1 subtraction + 100 demo trades + decision journaling

---

## 0. Audit Scope and Method

Examined the full codebase via direct read and dependency-graph survey. Evidence-based — every claim
below cites a specific file path and line range. This is a complement to `GROUND_TRUTH.md` (factual
state) and `CURRENT_PHASE.md` (gate progress).

The verdict is **operational, not analytical.** The GoldTrendFollowing strategy has plausible edge
per the WFO (3/3 folds profitable, OOS Sharpe 2.48). The danger lies in the substrate around it.

---

## 1. Current Architecture Assessment

### Strengths

- Async-first worker with `TaskSupervisor` restart logic (`worker_gold_bot.py:411-509`).
  Critical vs non-critical task distinction is correct.
- Clear `ExecutionState` machine in `trading_service.py`.
- Sequential gate stack (news → WS → market state → exchange health → volatility → spread → MQ → AI
  → router → strategy → dedup → risk).
- Reconciliation at three cadences (10s fast / 60s margin guard / 120s full).
- 101 test files including chaos network, concurrent risk, circuit breaker, exchange failover, crash
  recovery.
- Prometheus + Grafana + Loki + Promtail observability stack.
- GTF strategy has plausible WFO-validated edge.

### Weaknesses (S1 = critical, S2 = high, S3 = medium)

| Sev | Issue | Evidence |
|-----|-------|----------|
| S1 | `execute_trading_cycle` is one 580-line method | `app/execution/trading_service.py:372-949` |
| S1 | Duplicate authoritative modules (7 subsystems) | See §2 below |
| S1 | Risk authority fragmented across ≥8 modules | `risk/`, `infra/circuit_breaker`, `runtime/news_guard`, `strategy/market_state_filter`, `core/`, etc. |
| S1 | LLM on critical path | `trading_service.py:585-591` calls `orchestrator.run_paper_trade_cycle` |
| S2 | 11 dashboard files, 35 FastAPI routes | `app/dashboard/`, `app/main.py:35 includes` |
| S2 | 20 DB tables for 0 executed trades | `app/database/models.py` |
| S2 | 14+ classes in `app/resilience/` | `resilience_platform.py`, `resilience_manager.py`, etc. |
| S3 | Backup files committed (`*.backup.20260523_232248`) | `app/config.py.backup.*`, `app/logging_config.py.backup.*` |
| S3 | 10+ orphan tests in repo root | `test_bybit_client.py`, `test_enterprise_main.py`, etc. |
| S3 | Single notifier 1155 lines, single bybit_client 1906 lines | `app/notifications/notifier.py`, `app/infra/bybit_client.py` |

### Critical Risks

1. **Code-to-edge ratio is catastrophic.** 66,859 LOC for a strategy with 0 trades and t-test p=0.069.
2. **No single owner of trade-execution path.** Two trading services, two circuit breakers, two
   orchestrators, two strategy packages. Bug reasoning is impossible.
3. **LLM on the critical path** with no hard heuristic fallback. OpenRouter p99 = trade execution p99.
4. **Two force-pushes to main** observed in a single session. History rewrite on a deployed branch.
5. **Code added faster than removed.** This session alone: 3 new strategies + 1 reverted, main
   force-pushed twice, validation-phase rule implicitly suspended.

---

## 2. Complexity Analysis — Duplicated Subsystems

Every row below is a confirmed duplicate. Pick one, delete the other.

| Subsystem | Duplicate 1 (LOC) | Duplicate 2 (LOC) | Resolution |
|-----------|-------------------|-------------------|------------|
| Trading service | `app/execution/trading_service.py` (1984) | `app/services/trading_service.py` (218) | Keep execution/, delete services/ after verifying worker imports execution/ |
| Circuit breaker | `app/infra/circuit_breaker.py` (640) | `app/risk/circuit_breaker.py` (316) | Keep infra/, delete risk/ shim, update imports |
| Strategy package | `app/strategies/` (10 files) | `app/strategy/` (subdirs + helpers) | Merge into one — `app/domain/strategy/` recommended |
| AI orchestrator | `app/ai_agents/orchestrator.py` (1180) | `app/ai_agents/optimized_orchestrator.py` (556) | Pick one. If "optimized" is winning, replace original |
| Bybit client | `app/exchange/bybit_connector.py` (679, WS) | `app/infra/bybit_client.py` (1906, REST) | Either keep separated and rename for clarity, OR merge into one BybitExchange class with rest/ws submodules |
| Fault tolerance | `app/self_healing/watchdogs.py` (1445, 7 classes) | `app/resilience/` (14 classes, ~1500) | Collapse both into `app/runtime/health.py` + supervisor liveness timer (~400 lines total) |
| Simulation | `app/paper_trading/` (3 files) | `app/shadow_mode/execution_engine.py` | Pick one |

### Anti-Patterns Observed

- **God object** — `trading_service.py` (1984), `bybit_client.py` (1906), `watchdogs.py` (1445),
  `main.py` (1322), `risk_engine.py` (1223), `orchestrator.py` (1180), `notifier.py` (1155).
- **"Optimized" copy-rename** — `optimized_orchestrator.py` alongside the original. Classic
  refactor-abandonment indicator.
- **Defensive imports that hide failures** — `try: import pandas as pd; except ImportError: pass`
  at `gold_trend_following.py:353-356`. Silent disable if dependency breaks at runtime.
- **Module-level mutable singletons** — `_SHARED_INFERENCE_CACHE`, `_shared_news_guard`,
  `get_system_circuit_breaker()`. Untestable, not thread-safe across processes.
- **Layered defense without unified audit trail** — 12 gates, 12 different modules, each owns its
  own veto, no single `decision_journal` row per cycle.

---

## 3. Execution Path Analysis — Full Lifecycle Trace

One tick of `execute_trading_cycle(symbol="XAUUSDT")`:

```
[T+0ms]    worker_gold_bot.signal_scanning_loop
              ├── circuit_breaker.state OPEN? sleep 60, retry
              ├── position_sync.is_websocket_stale(>30s)? sleep 10, retry
              ├── news_guard.refresh_calendar_if_stale (HTTP on stale only)
              ├── news_guard.enforce_safety_check
              └── risk_engine._trading_paused? sleep 300, retry
[T+~5ms]   LiveTradingService.execute_trading_cycle (DB session opened)
              [Gate 1]  self_healing.health_decision               ← can block
              [Gate 2]  news_guard.is_trading_safe                  ← can block
              [Gate 3]  websocket_manager.is_data_stale(30s)        ← can block
              [Gate 4]  market_state_filter.evaluate                ← can block
              [Gate 5]  exchange_health.evaluate                    ← can block, can degrade size
              [Gate 6]  STATE: IDLE → FETCHING_DATA
[T+~50ms]     _fetch_market_data
                  ├── exchange_manager.fetch_ticker (REST, timeout 10s)
                  ├── exchange_manager.fetch_ohlcv 1h limit=250 (REST, timeout 20s)
                  └── exchange_manager.fetch_ohlcv 4h limit=300 (REST, timeout 20s)
                  └── RegimeDetector.detect (pandas, 10–50ms)
[T+~250ms]    [Gate 7]  risk_engine.check_volatility_chaos          ← can block
[T+~260ms]    [Gate 8]  risk_engine.check_slippage_risk             ← can block
[T+~310ms]    [Gate 9]  MarketQualityScorer.score                   ← can block
[T+~315ms]    STATE: FETCHING_DATA → ANALYZING
[T+~315ms]    orchestrator.run_paper_trade_cycle
                  ├── cache hit? use cached regime+strategy         [hot path, T+~320ms]
                  └── cache miss?
                      ├── Tier-1 LLM call (regime)        500–2000ms
                      ├── Tier-1 LLM call (strategy)      500–2000ms
                      └── Tier-2 LLM call (risk)         1000–3000ms  ← outsized latency
[T+~5500ms]   [Gate 10] StrategyRouter.generate_signal              ← can return None
              ├── quantity sizing (max_notional × mq_mult × conf / entry × leverage)
              └── adaptive_risk calc (unused for sizing, only logged)
[T+~5510ms]   STATE: ANALYZING → PROPOSING
[T+~5510ms]   [Gate 11] self_healing.guard_signal (dedup)           ← can block
[T+~5515ms]   STATE: PROPOSING → VALIDATING
[T+~5515ms]   [Gate 12] risk_engine.check_trade_approval (6 sub-guards) ← can block
[T+~5530ms]   STATE: VALIDATING → EXECUTING
[T+~5530ms]   _execute_trade (lines 1204–1510, 306 lines)
                  ├── precision normalization
                  ├── self_healing.execute_with_observation wraps:
                  └── create_market_order (Bybit V5 REST)            200–1500ms
[T+~7000ms]   anomaly detection on response
                  └── if pause_for_anomalies: STATE = paused_due_to_anomalies
[T+~7010ms]   DB write: TradeProposals, Trades, Positions, OrderEvents
[T+~7050ms]   STATE: EXECUTING → MONITORING
[T+~7050ms]   notifier.send (Telegram, fire-and-forget)
[T+~7100ms]   cycle complete → sleep 60s
```

### Latency / Failure Points

| Rank | Source | Typical | Worst case | Mitigation today |
|------|--------|---------|------------|------------------|
| 1 | LLM cache miss (3 calls) | 2–4s | 30s+ on OpenRouter slow path | 20s cache + background warm |
| 2 | OHLCV fetch (1H + 4H) | 200–500ms | 20s (timeout × 3 retries) | Timeout + retry |
| 3 | Order placement | 200–1500ms | timeout × retry | self_healing wrapper |
| 4 | DB writes per cycle | 50–200ms | pool exhaust at high concurrency | DB_POOL_SIZE=10 |
| 5 | Pandas math in `_fetch_market_data` | 10–50ms | linear in OHLCV length | none |
| 6 | News calendar refresh | rare (daily) | 5s blocking on stale | guarded by `is_stale` |

### Key Observations

- **End-to-end latency to fill: ~7 seconds on cache miss.** Fine for 1H bars, fatal for sub-5min.
- **12 sequential gates at 99% pass each → ~88.6% cumulative pass.** ≈11% of valid signals are
  filtered by gate compounding alone.
- **No single audit trail of "which gate blocked this cycle."** Block reasons in stderr only.
- **State machine is fragile sequential pipeline**, not actually a state machine. Inline
  `_transition_to()` calls with no recovery.

---

## 4. Production-Grade Target Architecture

Same capabilities, ~25,000 LOC instead of 66,859.

### Service Topology

```
                  ┌─────────────────────────────────────────────────┐
                  │ Postgres (single instance)                      │
                  │ Redis (cache only — never source of truth)      │
                  └─────────────────────────────────────────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
            ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐
            │  Worker   │   │  Control    │   │  Metrics  │
            │ (trading) │   │ Plane (API) │   │ Prometheus│
            └─────┬─────┘   └─────────────┘   └───────────┘
                  │
            ┌─────▼────────────────────────────────┐
            │   Bybit REST + WebSocket (one client) │
            └──────────────────────────────────────┘
```

Drop Loki + Promtail unless logs volume justifies them. Drop Grafana if dashboards are not actively
used. **3 containers, not 7.**

### Module Structure

```
app/
├── domain/                # pure logic, zero I/O
│   ├── strategy.py        # ONE strategy (GoldTrendFollowing)
│   ├── indicators.py      # EMA, RSI, ATR, ADX, VWAP — pure functions
│   ├── regime.py          # regime classification — pure function
│   └── signal.py          # SignalProposal dataclass
├── execution/
│   ├── pipeline.py        # ONE execute_cycle, ≤400 lines
│   ├── gates.py           # all 12 gates as composable Gate(name, check_fn)
│   ├── exchange.py        # single BybitClient, ≤500 lines
│   └── reconciler.py      # ONE reconcile loop (not three)
├── risk/
│   └── engine.py          # ≤400 lines, owns ALL risk decisions
├── infra/
│   ├── db.py
│   ├── repositories.py    # all DB queries
│   ├── circuit_breaker.py # ONE, here
│   └── kill_switch.py
├── api/
│   ├── app.py             # FastAPI, ≤300 lines
│   ├── trading.py         # 5 endpoints: health, positions, trades, pause, resume
│   └── status.py          # one read-only dashboard JSON endpoint
├── observability/
│   ├── metrics.py
│   └── logging.py
├── worker.py              # ≤200 lines, supervised tasks
└── config.py              # ≤300 lines, no backup file
```

**Target: every file under 500 lines. Every module has one owner.**

### Concurrency Model

Three async tasks, not ten:

1. **trade_loop** — fetches market data, runs pipeline, places orders
2. **reconciler_loop** — one reconcile every 30s (combine fast + full)
3. **liveness_loop** — writes heartbeat + health endpoint state

Position sync becomes part of reconciler. Margin guard becomes a risk check inside the pipeline.
Heartbeat monitor merges into liveness. Background LLM inference becomes optional and explicit.

### Risk Authority

One module. `app/risk/engine.py` owns: position limits, drawdown, circuit breaker state, kill
switch reads, daily loss, consecutive losses, news guard, exchange health, slippage, volatility,
dedup. No risk decision lives outside this file.

### LLM Placement

**Off the critical path.** Background task fills `inference_cache` every 20s. Hot path:
- If cache is fresh: use it
- If cache is stale: skip LLM, use heuristic (regime from rolling ATR/ADX)

Strategy never calls LLM directly.

---

## 5. Refactoring Plan — Prioritized

### Wave 1: Subtraction (1–2 weeks, zero functional change)

Pure deletion. No behaviour change. Each is independently revertible.

| # | Action | Files | Lines | Risk |
|---|--------|-------|-------|------|
| 1.1 | Delete backup files + add to `.gitignore` | `app/config.py.backup.*`, `app/logging_config.py.backup.*` | ~1,000 | None |
| 1.2 | Delete root-level orphan tests | 10 `test_*.py` in root | ~3,000 | None |
| 1.3 | Delete retired strategies | `gold_opening_reversal.py`, `gold_momentum_fade.py`, `gold_ultra_scalper.py`, `gold_bear_session_scalper.py` | ~1,800 | None |
| 1.4 | Delete unused strategy subdirs | `strategy/breakout/`, `strategy/mean_reversion/`, `strategy/trend/`, `strategy/ai_filter/`, `strategy/ensemble_combiner.py` | ~2,500 | Low |
| 1.5 | Archive non-Bybit exchange clients | `mexc_*.py`, `binance_client.py`, `app/exchange/mexc_*.py` | ~2,500 | None |
| 1.6 | Pick one of `paper_trading`/`shadow_mode`, archive other | One dir | ~500 | Low |
| 1.7 | Pick one of `optimized_orchestrator`/`orchestrator`, delete other | One file | ~600 | Medium |
| 1.8 | Delete deprecated `risk/circuit_breaker.py` shim | One file | 316 | Medium |
| 1.9 | Delete `app/services/trading_service.py` | One file | 218 | Low |
| 1.10 | Delete `app/learning/`, `app/replay/` if unused | Two dirs | ~2,000 | Medium |
| 1.11 | Merge `app/strategies/` + `app/strategy/` into `app/domain/` | All strategy files | 0 net | Medium |
| | **Wave 1 total** | | **~15,000** | |

After Wave 1: ~52,000 LOC, mental model tractable.

### Wave 2: Split God Objects (3–4 weeks, structure change, medium risk)

| # | Action | Target | Risk |
|---|--------|--------|------|
| 2.1 | Split `trading_service.py:execute_trading_cycle` into `pipeline.py` + `gates.py` | 1984 → 2× ~400 | Medium |
| 2.2 | Split `bybit_client.py` (1906) into `bybit_rest.py` + `bybit_ws.py` + `bybit_models.py` | ~600 each | Medium |
| 2.3 | Split `watchdogs.py` (1445) — keep only `QueueWatchdog`; replace others with supervisor timer | 1445 → ~100 | Medium |
| 2.4 | Collapse `resilience/` 14 classes into `app/risk/circuit_breaker.py` + `app/runtime/health.py` | ~1500 → 400 | High |
| 2.5 | Move all DB writes from `trading_service.py` to `app/database/repositories.py` | -300 from trading_service | Medium |
| 2.6 | LLM call off cycle — orchestrator becomes background cache-filler only | trading_service drops LLM await | Medium |
| 2.7 | Consolidate 11 dashboard files into 2 | 11 → 2 | Medium |

After Wave 2: ~35,000 LOC. Every file under 500.

### Wave 3: Harden Execution (2–3 weeks, low risk after Wave 2)

| # | Action | Why |
|---|--------|-----|
| 3.1 | Every gate writes structured row to `decision_journal` with `block_reason`, current values, thresholds | Per-cycle telemetry — no more guessing why trades didn't fire |
| 3.2 | Idempotent order placement: client-supplied `orderLinkId`, dedup at exchange + DB | Eliminates duplicate-fill class of bugs |
| 3.3 | Single reconciler at 30s (merge fast + full + position_sync) | -2 async tasks |
| 3.4 | LLM fully off critical path: heuristic fallback always exists | Cycle latency < 1s on cache miss |
| 3.5 | Inject all dependencies into `LiveTradingService.__init__` | Testability |

---

## 6. Performance Optimization Plan

### CPU
- Cache `RegimeResult` against bar timestamps — no recomputation until new 1H bar closes (~30–50ms/cycle).
- Lazy-import pandas/pybit at first use, not at boot (worker startup currently ~2 minutes).

### RAM
- Replace 7 watchdog classes with supervisor liveness timer.
- Confirm `_SHARED_INFERENCE_CACHE` eviction in `dedup_cleanup_loop`.
- Drop INFO log level for gate-passes; keep INFO only for blocks. ~120k log lines/week → ~10k.

### WebSocket
- Audit `websocket/manager.py` (702 lines) for unused reconnect/auth branches.
- Verify REST sync updates the WS-staleness heartbeat (currently asserted in GROUND_TRUTH).

### Async
- Worker tasks: 10 → 3 (trade, reconcile, liveness).
- Pick one reconciler (currently `run_periodic_reconciliation` + `reconciliation_service.reconcile`).
- Bulkhead LLM `aiohttp.ClientSession` from exchange/REST session.

### DB
- `DB_POOL_SIZE=10, DB_MAX_OVERFLOW=20, DB_POOL_TIMEOUT=15` is fine for one worker.
- Don't move to long-lived sessions — connection leaks bite hard.

---

## 7. Reliability Hardening

### Watchdogs
Replace 7 watchdog classes (1445 LOC) with:
1. Supervisor liveness check — task hasn't recorded progress in N minutes → restart.
2. Health endpoint exposing `last_cycle_completed_at`, `last_ws_message_at`, `last_db_query_at`,
   `current_state`. External Prometheus alert calls this.

### Idempotent Order Handling (highest impact)

```python
# Before placing order:
client_order_id = f"{strategy}_{symbol}_{int(time.time()*1000)}"
async with db:
    await db.insert(PendingOrder(client_order_id=client_order_id, ...))
    await db.commit()

# Place order:
try:
    response = await exchange.create_order(client_order_id=client_order_id, ...)
except Exception:
    # On any failure, reconciler will check exchange for client_order_id
    # within 30s. If found, mark filled. If not, mark cancelled.
    raise

# On success:
async with db:
    await db.update(PendingOrder, status="confirmed", exchange_order_id=response.order_id)
```

Today `_execute_trade` writes to DB *after* REST call — timeout-during-fill creates orphan position.
GROUND_TRUTH confirms this happened once: "ORPHANED_RECOVERED position." Bybit V5 supports
`orderLinkId` for exactly this.

### Recovery
- Reconciler audit log: every cycle writes one row to `sync_logs` (what was found vs expected).
- Circuit breaker: add HALF_OPEN auto-probe after 5 min to avoid manual reset.

---

## 8. Final Verdict — DANGEROUS for Live Capital

Not because the strategy logic is bad. Because:

1. No production system should have **two trading services, two circuit breakers, two orchestrators,
   two strategy packages.** When a bug appears, you cannot reason about which is canonical.
2. No production system should pull **LLM completions onto the critical path of trade execution**
   without a hard heuristic fallback.
3. No production system should allow **12 sequential gates with no unified audit trail.**
4. No production system should accept **new strategy code at the rate this session demonstrated** —
   3 new strategies + 1 reverted in <24h, main force-pushed twice. Code-on-top-of-code.
5. **Force-push-friendly main** is a production risk on its own. Branch protection should be enabled.

### Required State for Going Live

- Wave 1 subtraction complete (~50k LOC, retired strategies gone)
- Single `trading_service.py`, single circuit breaker, single orchestrator path verified
- `client_order_id` idempotent ordering deployed
- Decision journal writes per-gate `block_reason` to DB
- LLM off critical path with heuristic fallback
- 100+ consecutive demo trades complete (currently 0/100)
- Branch protection on main, no force-push allowed
- Single dashboard surfacing: `current_state`, `last_cycle_at`, `last_block_reason`,
  `open_positions`, `daily_pnl`, `circuit_breaker`, `kill_switch`

Until then: **demo only.** Strategy edge unproven; operational substrate unsafe; codebase growing
faster than validation.

### The Deeper Observation

In one session: 3 strategies appeared, 1 was reverted, 2 backtest scripts added, an implementation
plan drafted, main force-pushed twice, validation-phase rule implicitly suspended. **Each decision
in isolation is defensible.** Cumulatively they form a pattern: complexity is being added faster
than edge is being demonstrated. The system has never traded profitably, and the M1/M3/M5 successor
strategy is already being designed.

The single highest-impact action in the next 7 days:

> **Run the existing GoldTrendFollowingStrategy in demo for 30 days while executing Wave 1
> subtraction in parallel.**

If GTF demonstrates edge: you have a proven strategy on a hardened substrate.
If it doesn't: you have a clean codebase to replace it.
Either outcome is better than the current trajectory.
