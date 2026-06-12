# a1_smc_momentum Strategy README

Original source: README (4).md upload 2026-06-12

---

## RECONCILIATION NOTE (2026-06-12)

The `strategy.py` skeleton is a DIFFERENT design from the locked A1 spec and
from the production wrapper at `ag/alpha/a1_smc_momentum/a1_alpha.py`.

Key conflicts:
1. Multi-timeframe inputs (H4+H1+M15 DataFrames) — not in locked A1 spec
   (A1_SMC_MOMENTUM_DECISION.md). Would require a new lock-before-look spec.
2. Imports `from smc_implementation_skeletons.order_block_detector import ...`
   — wrong path. Production detectors live in `ag/alpha/a1_smc_momentum/detectors/`.
3. Imports `from ag.risk.position_sizing import PositionSizer` — doesn't exist.
   The RiskEngine already enforces 0.5%/trade size cap (G4 guard).
4. `risk_per_trade = 0.0075` conflicts with locked 0.5% (0.005).
5. `obs[-3:]` — checks only last 3 OBs. The production `A1SmcMomentum` wrapper
   now tracks ALL unmitigated OBs to avoid the 1-trade-per-363-pair-days failure.

What IS good in this skeleton:
- OB + FVG alignment check (`aligned_fvg` logic) — this is exactly the WHERE
  confluence defined in the A1 spec (Z1 + Z2). Valid direction to add to a1_alpha.py
  AFTER Phase B MVP validates trade count.
- ATR-based stop/target calculation — already in `a1_alpha.py` as a placeholder.

### What's already in production

`ag/alpha/a1_smc_momentum/a1_alpha.py` (built 2026-06-12):
- Multi-OB tracking (all history, not just last 3)
- Per-filter rejection logging (NO_SWEEP, NO_CHOCH, etc.)
- PipelineConfig toggles each filter independently
- Phase B MVP mode: sweep+choch only first

Skeleton file: `skeletons/a1_strategy_skeleton.py`

---

Original README content:

**Status**: Skeleton v0.1 — Ready for Phase 2 development

## Core Logic
- Higher-timeframe bias via H4 BOS
- Entry on H1 Order Block + FVG confluence
- Strict risk management via shared risk modules
- Multi-timeframe confluence required (H4 + H1 + M15)

## Next Steps (Phase 2)
1. Add M15 refinement logic
2. Implement regime classifier integration
3. Add full backtest harness
4. Pass Validation Gate v1
