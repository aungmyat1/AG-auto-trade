# Test Plan (v1 planning doc)

Original source: TEST_PLAN.md upload 2026-06-12.

---

## RECONCILIATION NOTE (2026-06-12)

Most of this plan was already implemented before it arrived; a few items are
superseded by locked decisions. Map of plan → repo:

| Plan section | Repo reality |
|---|---|
| §3.1 SMC concept tests | `tests/unit/smc/` — 66 tests (OB 12, FVG 10, liquidity 9, BOS/ChoCH 8, displacement 8, pipeline 19) |
| §3.2 risk tests | `tests/unit/test_risk_engine.py` — all six guards incl. G5 leverage. **Kelly sizing, correlation limits, kill-switch module: REJECTED** — sizing is locked at 0.5%/trade (G4); a separate kill-switch/drawdown module would duplicate G1/G2 (CLAUDE.md rule 10); `emergency_stop()` needs owner approval (see `RISK_MODEL_SKELETONS_README.md`) |
| §3.3 gate tests | `tests/unit/test_validation_gate.py`, `test_cost_model.py`, `test_deflated_sharpe.py`, `test_lock_before_look.py` (CI-enforced threshold consistency) |
| §3.3 cost shock | `tests/validation/stress_tests/test_cost_shock.py` — real suite (the uploaded `test_cost_shock.py` was an `assert True` placeholder; not adopted) |
| §3.5 Telegram alerting | `tests/unit/test_monitoring.py` — **added 2026-06-12 from this plan** (was the one genuine gap) |
| §5.2/§5.3 integration / E2E | `tests/validation/test_full_pipeline_e2e.py` — **added 2026-06-12 from this plan**: stub alpha → RiskEngine (non-bypassable, verified blocking) → backtest harness → gate; plus stress suite (`test_regime_shift.py`, `test_synthetic_scenarios.py`) |
| §5.4 acceptance criteria (Sharpe ≥ 1.8, DD ≤ 12%, PF ≥ 1.6) | **SUPERSEDED — do not use.** The locked gate (`GATE_DECISION.md`, immutable, CI-checked) is the only acceptance bar: n ≥ 200, net PF > 1.25, WR > 45%, Sharpe > 1.2, DD < 15%, CPCV/WF/MC/DSR legs |
| §7 coverage ≥ 85% CI gate | Not adopted as a CI gate without owner decision; `pytest-cov` is available for ad-hoc measurement |
| TEST_STRUCTURE.md folder layout | Not adopted — the existing layout (`tests/unit/`, `tests/unit/smc/`, `tests/validation/stress_tests/`) predates it and restructuring adds churn with no coverage gain |
| Uploaded `conftest.py` fixture | Not adopted — `tests/conftest.py` and `stress_tests/synthetic.py` already provide richer fixtures |
| Uploaded `test_order_block.py` / `test_drawdown_monitor.py` | Not adopted — import non-existent modules (`smc_implementation_skeletons.*`, `ag.risk.drawdown_monitor`); real equivalents already exist / are rejected duplicates |

Test-data strategy correction: synthetic scenarios live in
`tests/validation/stress_tests/synthetic.py` — NOT `research_archive/`
(reserved for validated-negative results).

---

Original plan content follows (historical):

## 1. Test Objectives

- Verify correctness of all SMC concept detectors
- Validate risk management logic under all conditions
- Ensure the Validation Gate only passes strategies with positive expectancy
- Confirm system safety (kill switches, drawdown limits, secret scanning)
- Achieve high test coverage on core modules (>85%)
- Enable continuous regression testing via CI/CD

## 2. Test Levels

Unit (pytest) · Integration · Component (detectors, risk) · System/E2E
(backtest + gate) · Stress/Chaos · Acceptance (gate decision, owner).

## 3. Test Categories (abridged)

SMC concepts (OB, FVG with ATR filter, liquidity/stop hunts, BOS/CHOCH, MTF
confluence) · Risk (sizing, drawdown, kill switch, correlation, regime
scaling) · Gate (thresholds, walk-forward, purged k-fold, cost models, cost
shock +50% spread / 2× slippage) · Strategy (signal correctness, robustness,
net-of-cost expectancy) · Infrastructure (secret scan, CI, Telegram,
emergency stop, replay determinism) · Performance (speed, memory,
concurrency).

## 5.3 Stress Tests (mandatory for gate)

1. Walk-forward (minimum 4 folds)
2. Regime shift (trending → ranging → volatile)
3. Cost shock (+50% spread + 2× slippage)
4. Black swan replay (NFP, FOMC, flash crash)
5. 50+ synthetic SMC scenarios

## 8. Entry & Exit Criteria

Entry: code imports, unit tests written, test data available.
Exit: critical tests passing, coverage target met, stress tests complete,
validation report generated.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Overfitting to historical data | Walk-forward + purged k-fold |
| Cost model inaccuracy | Real broker statement validation |
| Kill switch failure | Multiple layers + manual override |
| Low test coverage | Coverage gates in CI |
