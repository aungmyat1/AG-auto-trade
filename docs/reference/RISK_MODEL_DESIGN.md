# Risk Model Design

**Production location:** `ag/risk/engine.py`

This document summarises the design decisions behind the v4 risk engine.
It is a reference artefact; the code is the authoritative source.

---

## Six Sequential Guards

Every entry path must call `RiskEngine.validate_entry()`.
Violation at any guard returns `approved=False`. Caller **must not bypass**.

| Guard | ID | Default | Description |
|---|---|---|---|
| Daily loss limit | G1 | 2 % | Sum of intraday PnL; resets at day boundary |
| Max drawdown from peak | G2 | 15 % | equity / peak_balance; matches GATE_DECISION.md |
| Consecutive-loss cooldown | G3 | 3 losses → 1 h | Prevents revenge trading after streak |
| Position size cap | G4 | 0.5 %/trade | Max fraction of account per single entry |
| Max leverage | G5 | 5× | Applied to futures contracts |
| Max concurrent positions | G6 | 3 | Open positions tracked in `open_positions` dict |

Weekly advisory: 6 % (not a hard guard — informational warning in `RiskDecision.warnings`).

---

## Data Model

```python
RiskConfig(
    max_daily_loss_pct=0.02,        # G1
    max_drawdown_pct=0.15,          # G2 — must match GATE_DECISION.md; do NOT relax
    max_consecutive_losses=3,       # G3
    cooldown_period_seconds=3600,   # G3
    max_position_size_pct=0.005,    # G4
    max_leverage=5,                 # G5
    max_concurrent_positions=3,     # G6
)

RiskDecision(
    approved: bool,
    violations: list[str],          # guard IDs that triggered
    warnings: list[str],            # advisory (weekly, etc.)
    risk_score: float,              # 0–100 composite
    daily_pnl_pct: float,
    current_drawdown_pct: float,
    cooldown_remaining_s: int,
)
```

---

## State lifecycle

```
RiskEngine.__init__()               # in-memory state; caller owns persistence
validate_entry(position_size_pct)   # check all 6 guards
open_position(trade_id)             # register in open_positions
record_trade_result(pnl_pct, ...)   # update daily_pnl, equity, streak
reset_daily()                       # call at midnight / session boundary
```

State is not persisted to disk by the engine. The execution layer (Phase 3)
owns serialisation if daily state must survive restarts.

---

## Design constraints

- **Thresholds match the locked gate.** G2 = 15 % max drawdown is the same value
  in `GATE_DECISION.md`. Never change one without changing the other — but
  `GATE_DECISION.md` is immutable, so neither should change.
- **No bypass path.** There is no flag, env var, or method to skip guards.
  Adding one violates CLAUDE.md rule 5.
- **Instrument-agnostic.** Engine receives PnL in percentage terms; no symbol
  or tick-size logic here (those belong in CostModel / execution).
- **No external I/O.** Engine is pure in-memory. Alerts go through
  `ag/monitoring/` (Telegram), not from inside this module.

---

## Skeletons that duplicate this engine (reference only)

`docs/reference/skeletons/kill_switch_skeleton.py` — covers G1+G2 at different
thresholds (3 %/10 %). **Do not integrate.** Thresholds conflict with locked gate.

`docs/reference/skeletons/drawdown_monitor_skeleton.py` — same duplication.
max_portfolio_dd=0.12 conflicts with G2 (0.15).

`docs/reference/skeletons/position_sizing_skeleton.py` — covers G4 (0.5 %/trade).
Already implemented. Use `RiskConfig.max_position_size_pct` instead.
