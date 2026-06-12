# Phase 1 Execution Runbook

## Goal
Complete Validation Infrastructure Hardening in 3 weeks.

---
## RECONCILIATION NOTE (2026-06-12)

The following items from this runbook are ALREADY DONE in the current repo:

- cost_models: `ag/validation/cost_model.py` has `CostModel.for_gc()` + `for_6e()`
  and `with_shock()` (added 2026-06-12)
- validation/gate/gate.py: full 9-metric battery (PF, Sharpe, DD, WR, CPCV, WF, MC, DSR) ✅
- walk-forward: `ag/validation/walk_forward.py` ✅ (tested)
- purged K-fold (CPCV): `ag/validation/cpcv.py` ✅ (tested)
- monte_carlo: `ag/validation/monte_carlo.py` ✅ (tested)
- SMC detectors: all 5 built in `ag/alpha/a1_smc_momentum/detectors/` ✅
- Signal audit framework: `ag/validation/signal_audit/` ✅

GATE THRESHOLD CONFLICT: This runbook's VALIDATION_GATE_SPEC.md uses sharpe ≥ 1.8,
DD ≤ 12%, PF ≥ 1.6. The locked GATE_DECISION.md uses sharpe > 1.2, DD < 15%, PF > 1.25.
The locked file cannot be changed — A2 was gated against it. New thresholds require a new
lock-before-look document applied to future alphas only (Gate v2).

LIVE DATA REPLAY: Blocked pending Databento subscription (G1_DATA_READINESS.md §5).

RESEARCH_ARCHIVE LOCATION: smc_concepts/ folder proposed in this runbook is wrong —
production detector code lives in ag/alpha/a1_smc_momentum/detectors/. research_archive/
is for validated-NEGATIVE results only.

REMAINING IMMEDIATE WORK (after reconciliation):
- New informational metrics: Calmar, Recovery Factor, max consec losses, time-in-DD
- Cost shock testing (with_shock() wired into stress tests)
- Stress test suite (tests/validation/stress_tests/)
- Synthetic SMC scenario generators (50+ scenarios)
- Regime shift test harness

---

## Week 1: Cost Models + Gate Hardening

### Day 1–2
- [ ] Create `cost_models/` package with `spread_model.py`, `slippage_model.py`, `commission_model.py`
- [x] Implement `TotalCostCalculator` — done as `CostModel` in `ag/validation/cost_model.py`
- [ ] Integrate cost models into existing backtest engine

### Day 3–4
- [x] Enhance `validation/gate/gate.py` with new metrics (Expectancy, Calmar, Recovery Factor)
  — Expectancy already in `BacktestResult.expectancy_r`; Calmar/Recovery added 2026-06-12
- [ ] Implement live data replay engine (bar-by-bar mode first) — BLOCKED (Databento)
- [x] Add cost shock injection capability — `CostModel.with_shock()` added 2026-06-12

### Day 5
- [ ] First full gate run using cost models on a simple moving average strategy (baseline)
- [ ] Document results in `VALIDATION_STATUS.md`

## Week 2: Stress Tests + Synthetic Scenarios

### Day 1–3
- [x] Build stress test suite under `tests/validation/stress_tests/` — added 2026-06-12
- [x] Walk-forward + purged K-fold — already in ag/validation/ (tested)
- [x] Regime shift test harness — added 2026-06-12

### Day 4–5
- [x] Generate synthetic SMC scenarios — added 2026-06-12
- [x] Run all stress tests on baseline strategy — added 2026-06-12
- [ ] Achieve ≥80% pass rate on synthetic tests — measure after data

## Week 3: SMC Filter Builder v2 + Documentation

### Day 1–2
- [ ] Update `smc-filter-builder` skill

### Day 3
- [ ] Add one new concept (e.g., Breaker Block) using the new skill end-to-end

### Day 4–5
- [ ] Write `docs/PHASE1_COMPLETION_REPORT.md`
- [ ] Update `PROJECT_STATE.md`
- [ ] Final gate decision matrix review and approval

---

## Daily Rituals
- Every morning: Update `PROJECT_STATE.md` with progress
- Every evening: Run full test suite (`pytest`)
- Use `/smc-review` command before merging any new concept

## Success Criteria
Phase 1 is complete only when **all** items in the Acceptance Criteria section of
`PHASE1_TECHNICAL_SPEC.md` are checked.

NOTE: "All 21 existing tests still pass" in the spec should read "All existing tests still
pass" — as of 2026-06-12 the suite has 173+ tests, not 21.
