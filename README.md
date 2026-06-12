# AG Auto Trade

Validation-first futures trading system. The gate is the asset; strategy is a candidate.

## Build order (v4 plan)

1. ✅ Validation core — plain Python, zero engine dependency
2. ✅ Risk engine (6 sequential guards) + regime classifier (4 regimes)
3. ⬜ Alpha modules: A1 (SMC-filter+momentum), A2 (master-trader), A3 (ensemble)
4. ⬜ Gate race: all three through identical gate (cloud MAIN, compute-heavy)
5. ⬜ Execution (Nautilus + IB) — only if a ROBUST alpha exists

## Instruments

GC/MGC (gold futures) + 6E (euro FX futures) via CME/COMEX

## Data / Venue

- Historical: Databento (CME coverage) — Phase 1
- Live: Interactive Brokers — Phase 3 only

## Gate thresholds (pre-registered, locked before data)

See `ag/validation/lock_before_look/GATE_DECISION.md`

Quick summary: n ≥ 200 · net PF > 1.25 · Sharpe > 1.2 · max DD < 15% · CPCV + WF + MC + DSR intact

## Key constraint

**SMC = context filter only.** FRAGILE verdict from prior system (crypto SMC H1: CPCV 0.92, MC 0.89).
SMC answers WHERE; momentum/delta answers WHEN. SMC never generates entries.

## Quick start

```bash
cd ag-auto-trade
.venv/bin/python3 -m pytest tests/ -v              # 21 tests, all green
.venv/bin/python3 scripts/run_gate.py --help       # gate CLI
```

## Alpha status

See `VALIDATION_STATUS.md`

## Architecture

```
ag/validation/      VALIDATION CORE — built first, gate is the asset
ag/risk/            Risk engine — 6 sequential guards, non-bypassable
ag/regime/          Regime classifier — ADX/ATR/HTF, 4 regimes
ag/alpha/           Alpha interface + 3 stubs (A1/A2/A3), built after gate locked
  a1_smc_momentum/  SMC filter + momentum/delta trigger
  a2_master_trader/ SignalStart copy-trade (data in data/master_traders/)
  a3_ensemble/      Ensemble score > 0.75
ag/data/            Databento + IB live (Phase 1+)
ag/execution/       Nautilus L3 + IB venue (Phase 3 only)
ag/monitoring/      Telegram alerts (stdlib, no bloat)
research_archive/   Validated NEGATIVE results — never deleted, never re-run
```
