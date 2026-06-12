# AG-auto-trade Complete Roadmap (v1 planning doc)
**Saved**: 2026-06-12
**Note**: This is the v1 planning document. Current actual state is in docs/PROJECT_STATE.md.
A2 is already built and gated (READ verdict). A1 spec is locked. See PROJECT_STATE.md for live status.

---

**Project Goal**: Build a profitable, production-grade SMC (Smart Money Concepts) trading bot with rigorous validation gates before any live capital exposure.
**Current Date**: 2026-06-12
**Current Status**: Phase 0 complete — Trading Engineering OS baseline (21/21 tests, safety hooks, agent skills). All alpha strategies in PENDING validation.

---

## Vision
Deliver a fully automated SMC trading system that:
- Trades profitably on live markets (target: positive expectancy + controlled drawdown)
- Uses strict validation gates before live trading
- Maintains institutional-grade risk management and auditability
- Evolves via research → validation → live deployment loop

---

## Current State (2026-06-12)
- ✅ Trading Engineering OS v4 layer active (CLAUDE.md, PROJECT_STATE.md, 7 skills, 6 slash commands)
- ✅ Safety infrastructure: secret-scan pre-commit, pytest pre-push, GATE_DECISION/LIVE_TRADING guards
- ✅ Validation core + risk engine + regime classifier present
- ✅ Research archive with legacy SMC failures documented
- ✅ CI/CD (GitHub Actions pytest)
- ❌ No live trading enabled
- ❌ No production alpha strategies validated
- ❌ No broker execution layer connected

---

## Phased Roadmap

### Phase 1: Validation Infrastructure Hardening (Target: 2–3 weeks)
**Objective**: Make the validation gate bulletproof and ready for real SMC alphas.

- [ ] Finalize `validation/gate/` with live data replay capability
- [ ] Implement `cost_models/` with realistic slippage, commission, and spread models (Databento/IBKR data)
- [ ] Add walk-forward optimization + purged K-fold CV to strategy-validator skill
- [ ] Build `smc-filter-builder` skill into a full SMC concept library (Order Blocks, FVG, Liquidity, BOS/CHOCH, etc.)
- [ ] Create synthetic + historical SMC scenario test suite
- [ ] Gate Decision Matrix v1: Sharpe > 1.8, Max DD < 12%, Profit Factor > 1.6, Minimum 200 trades

**Deliverables**:
- `docs/VALIDATION_GATE_V1.md`
- Passing synthetic SMC stress tests

### Phase 2: Alpha Development — a1_smc_momentum (Target: 4–6 weeks)
**Objective**: Build and validate the first production SMC strategy.

- [ ] Implement core SMC detectors (OB, FVG, Liquidity grabs, BOS)
- [ ] Add multi-timeframe confluence + session filters (London/NY)
- [ ] Regime classifier integration (trending vs ranging)
- [ ] Risk model: ATR-based stops, position sizing via Kelly + volatility targeting
- [ ] Full backtest on 5+ instruments (Forex majors + Gold)
- [ ] Pass Gate Decision Matrix (paper trading 30+ days simulated)

**Deliverables**:
- `alpha/a1_smc_momentum/` production module
- `research_archive/a1_validation_report.md`

### Phase 3: Additional Alphas + Ensemble (Target: 6–8 weeks)
- [ ] a2_master_trader (multi-concept SMC: inducement + displacement)
- [ ] a3_ensemble (meta-strategy combining a1 + a2 with dynamic allocation)
- [ ] Correlation & drawdown diversification logic
- [ ] Second validation gate pass (stricter criteria)

### Phase 4: Execution & Live Infrastructure (Target: 3–4 weeks, parallel with Phase 3 end)
- [ ] Interactive Brokers (IBKR) or Databento live data + execution layer
- [ ] Order management, retry logic, kill switch
- [ ] Telegram + email alerting (already partially present)
- [ ] VPS deployment runbook + monitoring dashboards
- [ ] Paper trading → small capital live transition plan

### Phase 5: Production Deployment & Continuous Improvement (Ongoing)
- [ ] Live trading with micro lot sizing
- [ ] Weekly performance review + automated anomaly detection
- [ ] Research pipeline for new SMC concepts
- [ ] Quarterly full system audit

---

## Success Metrics (Live Trading Targets)
- Minimum 6 months live track record
- Sharpe Ratio ≥ 1.8
- Max Drawdown ≤ 15%
- Profit Factor ≥ 1.7
- Win rate ≥ 48% with positive expectancy
- Zero catastrophic risk events (thanks to gates)

---

## Risk Management Philosophy
- Validation gate is non-negotiable — no live trading without passing
- Capital allocation starts tiny (0.5–1% risk per trade initially)
- Full kill switch + emergency liquidation procedures
- All strategies must survive regime shifts and black-swan stress tests

---

## Next Immediate Actions (This Week)
1. Clone repo locally and run full test suite
2. Review `docs/PROJECT_STATE.md` and update current status
3. Start Phase 1: harden validation gate with realistic cost models
4. Begin documenting SMC concepts in `research_archive/smc_concepts/`

**Status**: Roadmap approved. Proceed to Phase 1.
