# Risk Model Skeletons README

Original source: README (5).md upload 2026-06-12

---

## RECONCILIATION NOTE (2026-06-12)

Every concept in these skeletons is ALREADY IMPLEMENTED in `ag/risk/engine.py`.
DO NOT create `ag/risk/kill_switch.py` or `ag/risk/drawdown_monitor.py` —
that would be a duplicate subsystem (violates CLAUDE.md rule #10).

### What already exists

| Skeleton concept | Already in RiskEngine | Notes |
|---|---|---|
| KillSwitch daily loss check | G1 guard: `max_daily_loss_pct = 0.02` | Skeleton uses 3% — CONFLICTS with locked 2% |
| KillSwitch portfolio DD check | G2 guard: `max_drawdown_pct = 0.15` | Skeleton uses 10% — CONFLICTS with locked 15% |
| DrawdownMonitor.update() | `validate_entry()` internal check | Already tracked in RiskEngine state |
| DrawdownMonitor.reset_daily() | `record_trade_result()` daily reset | Already in engine |
| PositionSizer | G4 guard: size cap 0.5%/trade | `strategy.py` imports it — doesn't exist (not needed) |

### Genuinely new concept: emergency_stop()

KillSwitch has `emergency_stop(message)` — a manual halt method.
The RiskEngine doesn't have this.  If ever needed, add to RiskEngine:
```python
def emergency_stop(self, reason: str = "manual") -> None:
    self._emergency_halt = True
    self._halt_reason = reason
```
Requires a new test + owner approval before adding.

### Skeleton files (reference only)

- `skeletons/kill_switch_skeleton.py` — conflicts: thresholds 3%/10% vs locked 2%/15%
- `skeletons/drawdown_monitor_skeleton.py` — conflicts: max_portfolio_dd=0.12 vs locked 0.15

---

Original README content follows:

| File                    | Purpose                        | Status |
|-------------------------|--------------------------------|--------|
| `position_sizing.py`    | Dynamic volatility-targeted sizing | Ready |
| `drawdown_monitor.py`   | Real-time DD tracking + circuit breakers | Ready |
| `kill_switch.py`        | Automated + manual emergency stops | Ready |

Integration: import into validation gate, used by every alpha strategy,
unit tested under stress conditions.
