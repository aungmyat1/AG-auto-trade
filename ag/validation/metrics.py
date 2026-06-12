"""
BacktestResult and supporting types.

All trades are expressed as R-multiples (e.g. +2.0 = 2R win, -1.0 = 1R loss).
The gate runs on these; cost_model applies per-trade cost before net checks.
"""
from __future__ import annotations

from dataclasses import dataclass
import statistics
import math


@dataclass
class BacktestResult:
    """Container passed to ValidationGate.run()."""
    trades_r: list[float]              # per-trade R-multiples, chronological
    instrument: str = ""
    timeframe: str = ""
    start_date: str = ""
    end_date: str = ""
    n_trials: int = 1                  # independent param/threshold combos tried

    def __post_init__(self) -> None:
        if not self.trades_r:
            raise ValueError("trades_r must be non-empty")

    # ------------------------------------------------------------------
    # Convenience properties (gross, before cost)
    # ------------------------------------------------------------------

    @property
    def n(self) -> int:
        return len(self.trades_r)

    @property
    def profit_factor_gross(self) -> float:
        wins = sum(t for t in self.trades_r if t > 0)
        losses = abs(sum(t for t in self.trades_r if t < 0))
        if losses == 0:
            return float("inf") if wins > 0 else 1.0
        return wins / losses

    @property
    def win_rate(self) -> float:
        return sum(1 for t in self.trades_r if t > 0) / self.n

    @property
    def avg_win(self) -> float:
        wins = [t for t in self.trades_r if t > 0]
        return statistics.mean(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [t for t in self.trades_r if t < 0]
        return statistics.mean(losses) if losses else 0.0

    @property
    def expectancy_r(self) -> float:
        return statistics.mean(self.trades_r) if self.trades_r else 0.0

    @property
    def sharpe_annualized(self) -> float:
        if self.n < 2:
            return 0.0
        mu = statistics.mean(self.trades_r)
        sigma = statistics.stdev(self.trades_r)
        if sigma == 0:
            return 0.0
        # Annualize assuming 252 trades/year (conservative for intraday)
        return (mu / sigma) * math.sqrt(252)

    @property
    def max_drawdown(self) -> float:
        """Max drawdown as a fraction (0–1) using 0.5% risk/trade."""
        risk_per_trade = 0.005
        equity = 1.0
        peak = 1.0
        max_dd = 0.0
        for r in self.trades_r:
            equity = equity * (1.0 + r * risk_per_trade)
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    # ------------------------------------------------------------------
    # Informational properties — not gate criteria (gate thresholds are
    # locked in GATE_DECISION.md and cannot be changed without a new
    # lock-before-look commit).  These feed future Gate v2 analysis only.
    # ------------------------------------------------------------------

    @property
    def calmar_ratio(self) -> float:
        """CAGR / max_drawdown. Returns 0.0 if max_drawdown is 0."""
        md = self.max_drawdown
        if md == 0.0:
            return 0.0
        risk = 0.005
        equity = 1.0
        for r in self.trades_r:
            equity *= (1.0 + r * risk)
        years = self.n / 252.0
        if years <= 0:
            return 0.0
        cagr = equity ** (1.0 / years) - 1.0
        return cagr / md

    @property
    def recovery_factor(self) -> float:
        """Net profit / max_drawdown. Returns 0.0 if max_drawdown is 0."""
        md = self.max_drawdown
        if md == 0.0:
            return 0.0
        risk = 0.005
        equity = 1.0
        for r in self.trades_r:
            equity *= (1.0 + r * risk)
        return (equity - 1.0) / md

    @property
    def max_consecutive_losses(self) -> int:
        """Longest streak of consecutive losing trades."""
        max_streak = current = 0
        for t in self.trades_r:
            if t < 0:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        return max_streak

    @property
    def time_in_drawdown_pct(self) -> float:
        """Fraction of trades where equity is below its prior peak."""
        risk = 0.005
        equity = peak = 1.0
        count = 0
        for r in self.trades_r:
            equity *= (1.0 + r * risk)
            if equity < peak:
                count += 1
            else:
                peak = equity
        return count / self.n
