# AG-auto-trade — Complete Documentation & Deliverables Index

Generated: 2026-06-12
Reconciled against live repo state as of commit bb84a67.

---

## RECONCILIATION NOTE

The "30+ artifacts" original index describes planning material.
Most of it is already implemented in the production codebase.
This file maps each listed artifact to its actual status.

---

## 1. Strategic Docs

| File | Location | Status |
|---|---|---|
| ROADMAP.md | `docs/reference/ROADMAP_v1.md` | Saved (reference) |
| PROJECT_OVERVIEW.md | `docs/reference/PROJECT_OVERVIEW.md` | Saved (reference) |
| CURRENT_STATUS_SUMMARY.md | `docs/reference/CURRENT_STATUS_SNAPSHOT_2026-06-12.md` | Saved (STALE — see actual `docs/PROJECT_STATE.md`) |
| VALIDATION_GATE_SPEC.md | `docs/reference/VALIDATION_GATE_SPEC.md` | Saved with conflict note (Gate v2 thresholds, not locked) |
| PHASE1_TECHNICAL_SPEC.md | `docs/reference/PHASE1_TECHNICAL_SPEC.md` | Saved with reconciliation |
| PHASE1_RUNBOOK.md | `docs/reference/PHASE1_RUNBOOK.md` | Saved with reconciliation |
| RISK_MODEL_DESIGN.md | `docs/reference/RISK_MODEL_SKELETONS_README.md` | Saved; concepts already in RiskEngine |
| SMC_CONCEPT_LIBRARY.md | `docs/reference/SMC_CONCEPT_LIBRARY.md` | Saved (reference) |

**Ground truth**: `docs/PROJECT_STATE.md` (updated every session).

---

## 2. Production Code (already in repo)

| Concept | Production location | Notes |
|---|---|---|
| OB detector | `ag/alpha/a1_smc_momentum/detectors/order_block.py` | Built + tested |
| FVG detector | `ag/alpha/a1_smc_momentum/detectors/fvg.py` | Built + tested |
| Liquidity/sweep detector | `ag/alpha/a1_smc_momentum/detectors/liquidity.py` | Built + tested |
| BOS/CHOCH detector | `ag/alpha/a1_smc_momentum/detectors/bos_choch.py` | Built + tested |
| Displacement detector | `ag/alpha/a1_smc_momentum/detectors/displacement.py` | Built + tested |
| Risk engine (6 guards) | `ag/risk/engine.py` | Built + tested (replaces kill_switch + drawdown_monitor) |
| A1 alpha module | `ag/alpha/a1_smc_momentum/a1_alpha.py` | Built with multi-OB tracking |
| A2 alpha module | `ag/alpha/a2_master_trader/a2.py` | Built; READ verdict 2026-06-12 |
| SMC pipeline | `ag/alpha/a1_smc_momentum/pipeline.py` | Built (composable, Phase B MVP config) |
| Signal audit tracker | `ag/validation/signal_audit/tracker.py` | Built |
| Validation gate | `ag/validation/gate.py` | Built; 9-metric battery; thresholds LOCKED |
| Cost model | `ag/validation/cost_model.py` | Built; with_shock() added |
| BacktestResult metrics | `ag/validation/metrics.py` | +4 informational metrics added |
| Telegram monitoring | `ag/monitoring/__init__.py` | stdlib-only (no requests) |
| Regime classifier | `ag/regime/classifier.py` | Built + tested |

---

## 3. Reference-Only Skeletons (docs/reference/skeletons/)

| Skeleton | Conflict / Reason not in production |
|---|---|
| `kill_switch_skeleton.py` | Duplicate of RiskEngine G1+G2; thresholds conflict |
| `drawdown_monitor_skeleton.py` | Same; max_portfolio_dd=0.12 conflicts with locked 0.15 |
| `a1_strategy_skeleton.py` | Wrong imports; obs[-3:] failure mode; multi-TF not in locked spec |
| `telegram_alert_skeleton.py` | Uses `requests`; production uses stdlib only |
| `backtest_engine_skeleton.py` | Wrong imports; exit logic bug; use BacktestResult+ValidationGate instead |

---

## 4. Templates (docs/reference/)

| Template | Purpose |
|---|---|
| `VALIDATION_REPORT_TEMPLATE.md` | Fill after every backtest before gate submission |
| `DOCS_INDEX.md` | Navigation guide |
| `FINAL_DELIVERABLES_INDEX.md` | This file |

---

## 5. Current Gaps (from docs/PROJECT_STATE.md)

| Gap | Blocked on |
|---|---|
| Lock-before-look loader (code reads GATE_DECISION.md) | Build with A1 gating |
| Phase B MVP lock spec (A0_MVP_DECISION.md) | Owner writes lock file first |
| Live data replay | Databento subscription |
| Gate race (A1/A2/A3) | Databento data + Phase B spec |
| Execution layer | ROBUST verdict (none exists yet) |

---

## Quick-start Commands

```bash
# Full test suite (must be green before any commit)
python3 -m pytest tests/ -q

# Gate a CSV of trades
python3 scripts/run_gate.py trades.csv --instrument GC --cost-preset gc --n-trials 1

# Signal pipeline audit (find the bottleneck)
python scripts/run_signal_audit.py --n-bars 500 --scenario trending

# A2 gate run
python scripts/run_a2_gate.py

# Lint
python3 -m ruff check ag/ tests/
```
