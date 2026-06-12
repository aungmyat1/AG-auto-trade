# REFERENCE SKELETON ONLY — do not import or run
# Source: drawdown_monitor.py upload 2026-06-12
#
# CONFLICTS WITH PRODUCTION CODE:
#   max_portfolio_dd = 0.12  →  RiskEngine.max_drawdown_pct = 0.15 (locked)
#   daily_limit = 0.03       →  RiskEngine.max_daily_loss_pct = 0.02 (locked)
#
# ALREADY COVERED BY: ag/risk/engine.py  (G1 + G2 guards + validate_entry())
# DO NOT create ag/risk/drawdown_monitor.py — duplicate subsystem.

class DrawdownMonitor:
    def __init__(self, max_portfolio_dd: float = 0.12, daily_limit: float = 0.03):
        self.max_portfolio_dd = max_portfolio_dd
        self.daily_limit = daily_limit
        self.peak_equity = 0.0
        self.daily_start_equity = 0.0

    def update(self, current_equity: float) -> dict:
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        drawdown = (self.peak_equity - current_equity) / self.peak_equity
        daily_loss = (
            (self.daily_start_equity - current_equity) / self.daily_start_equity
            if self.daily_start_equity else 0
        )

        status = {
            "drawdown": round(drawdown, 4),
            "daily_loss": round(daily_loss, 4),
            "breach": drawdown > self.max_portfolio_dd or daily_loss > self.daily_limit,
        }
        return status

    def reset_daily(self, equity: float):
        self.daily_start_equity = equity
