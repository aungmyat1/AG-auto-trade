# REFERENCE SKELETON ONLY — do not import or run
# Source: kill_switch.py upload 2026-06-12
#
# CONFLICTS WITH PRODUCTION CODE:
#   daily_loss > 0.03  →  RiskEngine.max_daily_loss_pct = 0.02 (locked)
#   portfolio_dd > 0.10 → RiskEngine.max_drawdown_pct = 0.15  (locked)
#
# ALREADY COVERED BY: ag/risk/engine.py  (G1 + G2 guards)
# DO NOT create ag/risk/kill_switch.py — duplicate subsystem.
#
# GENUINELY NEW: emergency_stop(message) — not yet in RiskEngine.
# If adding, requires a new test and owner approval.

class KillSwitch:
    def __init__(self):
        self.triggered = False
        self.reason = None

    def check(self, daily_loss: float, portfolio_dd: float) -> bool:
        if daily_loss > 0.03 or portfolio_dd > 0.10:
            self.triggered = True
            self.reason = f"Daily loss: {daily_loss:.2%} | Portfolio DD: {portfolio_dd:.2%}"
            return True
        return False

    def emergency_stop(self, message: str = "Manual emergency stop"):
        self.triggered = True
        self.reason = message
        # In real implementation: close all positions, disable trading
        print(f"[KILL SWITCH ACTIVATED] {message}")
