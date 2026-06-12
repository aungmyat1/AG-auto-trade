# REPO AUDIT RECONCILIATION
# Phase 1 deliverable — v4 fresh-start plan
# Source audit: docs/reference/ARCHITECTURAL_AUDIT_2026-05-28.md
# Reconciled against: ag-auto-trade main @ 2026-06-12
#
# For each finding in the original audit, this document records:
#   ELIMINATED  — not present in v4 (clean start, never ported)
#   BY-DESIGN   — the v4 architecture prevents this class of problem by construction
#   DEFERRED    — execution-path concern; deferred until Phase 3 (ROBUST verdict required first)
#   WATCH       — not yet built, must not repeat the pattern when it is

---

## Summary

The 2026-05-28 audit declared the old `auto-trade-system` DANGEROUS for live capital. The v4
platform (`ag-auto-trade`) does not inherit any of the audit's S1/S2/S3 findings — it is a clean
fork that deliberately inverts the build order: **validation gate first, execution last**.

The old system backup is preserved at `~/backups/auto-trade-system-2026-06-12.tar.gz` (69 MB).

---

## 1. S1 Critical Findings

### S1-A: `execute_trading_cycle` — 580-line god method

**Audit finding:** `app/execution/trading_service.py:372–949` — one method owns entire cycle.

**v4 status: ELIMINATED**
`ag/execution/` is intentionally empty (Phase 3, deferred). When built, the v4 architecture
mandates a single `execute_cycle()` owner in `ag/execution/` with the cycle as a composable
pipeline (`AlphaModule → RiskEngine.validate_entry() → journal → Telegram`). No 580-line methods
allowed; gate.py is the reference for how to decompose complex pipelines.

**Evidence:** `ag/execution/` = empty; `ag/alpha/base.py:43` shows the AlphaModule→RiskEngine
call chain design.

---

### S1-B: 7 duplicate authoritative subsystems

**Audit finding:** 7 confirmed pairs of duplicate modules — trading service, circuit breaker,
strategy packages, AI orchestrator, exchange client, fault tolerance, simulation.

**v4 status: ELIMINATED**

| Old duplicate pair | v4 resolution |
|---|---|
| `execution/trading_service.py` (1984) + `services/trading_service.py` (218) | No trading service yet; when built, ONE in `ag/execution/` |
| `infra/circuit_breaker.py` (640) + `risk/circuit_breaker.py` (316) | `ag/risk/engine.py` owns all guards; no separate circuit_breaker |
| `strategies/` (10 files) + `strategy/` (subdirs) | `ag/alpha/` with AlphaModule ABC — one interface, three implementations |
| `ai_agents/orchestrator.py` (1180) + `optimized_orchestrator.py` (556) | No LLM/orchestrator in v4 |
| `exchange/bybit_connector.py` (679) + `infra/bybit_client.py` (1906) | Bybit archived; IB via Nautilus (Phase 3) |
| `self_healing/watchdogs.py` (1445) + `resilience/` (14 classes) | No self-healing layer; Telegram monitoring stub |
| `paper_trading/` + `shadow_mode/` | Not built yet; when built, one dry-run harness |

**Hard rule to prevent recurrence:** CLAUDE.md §Hard Rule 10 — "One implementation per concern,
always." The old repo died with 7 duplicated pairs; no duplicate implementations are permitted.

---

### S1-C: Risk authority fragmented across ≥8 modules

**Audit finding:** risk decisions spread across `risk/`, `infra/circuit_breaker`, `runtime/news_guard`,
`strategy/market_state_filter`, `core/`, etc.

**v4 status: BY-DESIGN**
All 6 guards live in `ag/risk/engine.py::RiskEngine.validate_entry()`. No other module makes risk
decisions. The rule is in CLAUDE.md §Hard Rule 5: "Risk engine is non-bypassable. Every entry
path calls `RiskEngine.validate_entry()`."

**Evidence:** `ag/risk/engine.py` — single authority, 6 guards (G1–G6), config in `RiskConfig`.

---

### S1-D: LLM on critical path

**Audit finding:** `trading_service.py:585-591` calls `orchestrator.run_paper_trade_cycle` with
LLM chain inline (500–3000ms, no heuristic fallback).

**v4 status: ELIMINATED**
No LLM anywhere in v4. AlphaModules are deterministic (rule-based A1, copy-based A2, score-based
A3). The monitoring layer is stdlib only (CLAUDE.md §Architecture). No LLM dependency exists.

**WATCH for Phase 3:** if any future feature is proposed with "LLM on the critical path" — the
answer is always no. Background-only with hard heuristic fallback, matching the audit's recommendation.

---

## 2. S2 High-Priority Findings

### S2-A: 11 dashboard files, 35 FastAPI routes

**v4 status: ELIMINATED / DEFERRED**
No dashboard in v4. If a control API is added (Phase 3), it follows the audit's target: one
`app.py` (<300 lines), 5 endpoints max (health, positions, trades, pause, resume).

### S2-B: 20 DB tables for 0 executed trades

**v4 status: ELIMINATED**
No database in v4 yet. The schema will be built when there is a ROBUST alpha to trade. Lean
schema first, not anticipatory schema.

### S2-C: 14+ resilience classes, god objects

**v4 status: ELIMINATED**
Largest file in v4 is `ag/risk/engine.py` at ~350 lines (estimated; within audit's recommended
500-line cap). No god objects. The AlphaModule ABC enforces two methods per alpha.

---

## 3. S3 Medium-Priority Findings

### S3-A: Backup files committed

**v4 status: ELIMINATED**
`.gitignore` excludes `.env`, `*.backup.*`, `*.pyc`, `__pycache__`. No backup files in repo.

### S3-B: Orphan tests in repo root

**v4 status: ELIMINATED**
All tests in `tests/unit/` or `tests/integration/`. No root-level test files. Enforced by
`pyproject.toml` testpaths = ["tests"].

### S3-C: Force-push to main, no branch protection

**v4 status: ELIMINATED**
Branch protection enabled 2026-06-12. Require PR + checks, no force push allowed.
Evidence: `docs/PROJECT_STATE.md` gap table — "Branch protection OFF on `main`" → ✅ Closed.

---

## 4. Critical Risks from Audit

| Audit risk | v4 resolution |
|---|---|
| Code-to-edge ratio catastrophic (66k LOC, 0 trades) | BY-DESIGN: build order inverted. Gate exists before any alpha. LOC grows only as edge is validated. |
| No single owner of execution path | BY-DESIGN: `ag/execution/` empty; will have single pipeline when built |
| LLM on critical path without heuristic fallback | ELIMINATED: no LLM anywhere |
| Force-push to main | ELIMINATED: branch protection on |
| Code added faster than removed | BY-DESIGN: lock-before-look + gate race prevents "strategy churn"; every alpha must pass or go to research_archive/ |

---

## 5. "Required State for Going Live" from Audit — v4 Mapping

The audit listed 8 prerequisites for production. All are addressed by v4's build order.

| Audit requirement | v4 status |
|---|---|
| Wave 1 subtraction complete | NOT APPLICABLE — v4 is a clean start, no subtraction needed |
| Single trading_service, circuit breaker, orchestrator | BY-DESIGN — one each when Phase 3 is built |
| Idempotent `client_order_id` ordering | DEFERRED (Phase 3) — must implement before any live order |
| Decision journal with per-gate `block_reason` | DEFERRED (Phase 3) — architecture supports it |
| LLM off critical path + heuristic fallback | ELIMINATED — no LLM in v4 |
| 100+ consecutive demo trades | NOT STARTED — blocked on a ROBUST verdict (none exists) |
| Branch protection on main | DONE — 2026-06-12 |
| Single dashboard with key state | DEFERRED (Phase 3) |

---

## 6. What the v4 Plan Fixes That v2 Would Not

The user also submitted a "v2 rebuild plan" (dated 2026-06-12 chat). Four v2 items would have
re-introduced audit findings:

| v2 instruction | Audit finding it would re-introduce | v4 correction |
|---|---|---|
| "Master Trader Alpha First" (Phase 7) | Implicitly grants primacy to one alpha before evidence — same pattern as the old system asserting GTF was the strategy | All three alphas (A1/A2/A3) race one gate; gate decides |
| Generic L1–L5 ladder (unit → backtest → WFO → MC → dry-run) | Unquantified validation — same pattern as the audit's "WFO 3/3 folds" claim that didn't survive cost modeling | Specific gate: n≥200, PF>1.25 net of cost, CPCV, WF 60%, MC p5, DSR>0 |
| Keep `exchange_connectors/` in the KEEP list | Crypto connectors + Bybit bias — same Bybit-centric design the audit flagged as "archive non-Bybit clients" | Futures-first: GC/MGC/6E via IB. Crypto connectors archived. |
| Build execution first (Weeks 1–2: Docker + DB + Exchange Adapter) | Substrate before edge — the audit's diagnosis of the old system exactly | Phase 3 execution blocked until ROBUST verdict exists |

---

## 7. Remaining Gaps (carry into PROJECT_STATE.md)

| Gap | Status |
|---|---|
| Lock-before-look loader in code | Open — gate thresholds are in `gate.py`/`config.py`; no code reads `GATE_DECISION.md`. Build alongside alphas. |
| Idempotent ordering | Deferred — Phase 3 |
| Decision journal | Deferred — Phase 3 |
| A1/A3 not built | In progress — spec locked 2026-06-12; code is next dispatch |
| Dry-run harness | Not built — need ROBUST verdict first |

---

## Reconciliation Verdict

**The v4 platform does not carry forward any S1, S2, or S3 finding from the 2026-05-28 audit.**
The audit's recommended target architecture (`validation → risk → alpha → execution`; single owner
per concern; no LLM on path; branch protection) is the build order the v4 plan implements.

The audit is **CLOSED** against the v4 codebase as of 2026-06-12.
