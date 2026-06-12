# Phase 1 Technical Specification
**Phase**: Validation Infrastructure Hardening
**Duration**: 2–3 weeks
**Goal**: Make the validation gate production-ready and capable of rigorously testing SMC strategies with realistic market conditions.

---

## RECONCILIATION NOTE (2026-06-12)

Section 3.3's pseudocode (sharpe >= 1.8, max_dd <= 0.12, profit_factor >= 1.6) represents
GATE V2 thresholds that differ from the locked GATE_DECISION.md. These cannot be applied to
the existing gate.py because A2 was already gated under the current thresholds. Adding them
would violate the lock-before-look principle.

Path forward for Gate v2 thresholds:
1. Write ag/validation/lock_before_look/GATE_V2_DECISION.md (new lock file)
2. Gate v2 applies to A3 and future alphas ONLY
3. A1 and A2 verdicts remain under Gate v1 (current GATE_DECISION.md)
Owner must approve Gate v2 before committing the lock file.

New metrics (Calmar Ratio, Recovery Factor, max consecutive losses, time in drawdown)
have been added to BacktestResult as INFORMATIONAL properties. They are reported but
do not currently affect gate verdicts. They will feed into Gate v2 once locked.

---

## 1. Objectives

1. Harden `validation/gate/` with live data replay capability
2. Implement realistic `cost_models/` (slippage, spread, commission)
3. Expand `smc-filter-builder` skill into full SMC concept library integration
4. Build comprehensive stress test suite (walk-forward, regime shifts, cost shocks)
5. Create synthetic + historical SMC scenario test battery
6. Finalize Gate Decision Matrix v1 with strict thresholds

---

## 2. Deliverables

| Deliverable | Location | Owner |
|-------------|----------|-------|
| Validation Gate v1 | `validation/gate/gate.py` | Core team |
| Cost Models Module | `ag/validation/cost_model.py` | ✅ done |
| Cost shock injection | `CostModel.with_shock()` | ✅ done 2026-06-12 |
| New informational metrics | `BacktestResult` properties | ✅ done 2026-06-12 |
| SMC Filter Builder v2 | `.claude/skills/smc-filter-builder/` | Agent + dev |
| Stress Test Suite | `tests/validation/stress_tests/` | ✅ done 2026-06-12 |
| Synthetic SMC Scenarios | `tests/validation/stress_tests/synthetic.py` | ✅ done 2026-06-12 |
| Gate Decision Matrix v1 | `docs/VALIDATION_GATE_V1.md` | Documentation |

---

## 3. Validation Gate Enhancements

### 3.1 Live Data Replay Engine
- Support for replaying historical data tick-by-tick or bar-by-bar
- BLOCKED: Requires Databento subscription (see G1_DATA_READINESS.md §5)

### 3.2 Enhanced Metrics (added as informational to BacktestResult)
- ✅ Expectancy per trade (already existed as `expectancy_r`)
- ✅ Calmar Ratio (added 2026-06-12)
- ✅ Recovery Factor (added 2026-06-12)
- ✅ Maximum consecutive losses (added 2026-06-12)
- ✅ Time in drawdown (added 2026-06-12)

### 3.3 Gate Decision Logic (PROPOSED — Gate v2, NOT yet locked)
```python
# THIS IS NOT THE CURRENT GATE — these thresholds differ from locked GATE_DECISION.md
# Requires a new lock-before-look commit before use on any alpha
def evaluate_strategy(backtest_results):
    if (sharpe >= 1.8 and
        max_dd <= 0.12 and
        profit_factor >= 1.6 and
        trades >= 200 and
        expectancy > 0):
        return "GREEN"
    return "RED"
```

---

## 4. Cost Models Module

### 4.1 Components (all in `ag/validation/cost_model.py`)
- `CostModel` — spread_r + commission_r + slippage_r per trade
- `CostModel.for_gc()` — Gold futures preset
- `CostModel.for_6e()` — Euro FX futures preset
- `CostModel.with_shock(spread_mult, slippage_mult)` — cost shock testing ✅

### 4.2 Default Parameters
| Parameter              | Default Value     | Source          |
|------------------------|-------------------|-----------------|
| GC spread              | 0.07R             | CME tick data   |
| GC slippage            | 0.06R             | Conservative    |
| GC commission          | 0.05R             | CME standard    |
| 6E spread              | 0.04R             | CME tick data   |

### 4.3 Cost Shock Testing
- `+50% spread, 2× slippage` — `cm.with_shock(1.5, 2.0)` ✅
- Tests in `tests/validation/stress_tests/test_cost_shock.py` ✅

---

## 5. SMC Filter Builder Skill Expansion
(Pending — Week 3)

---

## 6. Stress Test Suite (`tests/validation/stress_tests/`)

### 6.1 Required Tests ✅ built 2026-06-12
1. **Cost Shock Test** — `test_cost_shock.py`
2. **Regime Shift Test** — `test_regime_shift.py`
3. **Synthetic Scenario Battery** — `test_synthetic_scenarios.py`

Walk-forward and CPCV already fully tested in `tests/unit/`.

### 6.2 Synthetic Scenarios (in `synthetic.py`) ✅
- Strong trend with pullbacks → expected ROBUST
- Choppy ranging market → expected FRAGILE (thin edge, cost drag)
- Liquidity grab + reversal → expected READ (n < 200)
- Failed breakout (inducement) → expected FRAGILE
- News spike with low count → expected FRAGILE (n < 50)

---

## 7. Acceptance Criteria for Phase 1 Completion

- [ ] All existing tests still pass (currently 173+; "21" in original spec was stale)
- [x] New stress test suite built (tests/validation/stress_tests/)
- [x] Cost models produce realistic P&L impact
- [x] New metrics (Calmar, Recovery Factor) available on BacktestResult
- [ ] Gate Decision Matrix v1 documented and owner-approved (needs Gate v2 lock decision)
- [ ] `smc-filter-builder` skill can successfully add and validate a new concept end-to-end
- [ ] Full Phase 1 runbook created in `docs/PHASE1_RUNBOOK.md`

---

**Status**: Spec reconciled. Infrastructure phase ~70% complete.
Blocked items: live data replay (Databento), Gate v2 threshold lock (owner decision).
