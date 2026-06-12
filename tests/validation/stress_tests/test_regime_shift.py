"""Regime shift stress tests.

Tests that the gate correctly distinguishes between trending and choppy
regimes, and that the new informational metrics also reflect regime changes.
"""
from __future__ import annotations

from ag.validation.gate import ValidationGate
from ag.validation.metrics import BacktestResult
from ag.validation.cost_model import CostModel
from .synthetic import (
    choppy_ranging,
    trend_with_pullbacks,
)

_gate = ValidationGate()
_cm = CostModel()


class TestRegimeMetricDifference:
    """Trending regime should dominate choppy on every quality metric."""

    def test_trending_better_gross_pf(self):
        trend = BacktestResult(trades_r=trend_with_pullbacks())
        chop = BacktestResult(trades_r=choppy_ranging())
        assert trend.profit_factor_gross > chop.profit_factor_gross

    def test_trending_better_sharpe(self):
        trend = BacktestResult(trades_r=trend_with_pullbacks())
        chop = BacktestResult(trades_r=choppy_ranging())
        assert trend.sharpe_annualized > chop.sharpe_annualized

    def test_trending_smaller_drawdown(self):
        trend = BacktestResult(trades_r=trend_with_pullbacks())
        chop = BacktestResult(trades_r=choppy_ranging())
        assert trend.max_drawdown < chop.max_drawdown

    def test_trending_better_calmar(self):
        trend = BacktestResult(trades_r=trend_with_pullbacks())
        chop = BacktestResult(trades_r=choppy_ranging())
        assert trend.calmar_ratio > chop.calmar_ratio

    def test_trending_better_recovery_factor(self):
        trend = BacktestResult(trades_r=trend_with_pullbacks())
        chop = BacktestResult(trades_r=choppy_ranging())
        assert trend.recovery_factor > chop.recovery_factor

    def test_trending_less_time_in_drawdown(self):
        trend = BacktestResult(trades_r=trend_with_pullbacks())
        chop = BacktestResult(trades_r=choppy_ranging())
        assert trend.time_in_drawdown_pct < chop.time_in_drawdown_pct


class TestRegimeGateVerdicts:
    """Gate should produce different verdicts for different regimes."""

    def test_trending_robust_choppy_fragile(self):
        v_trend = _gate.run(BacktestResult(trades_r=trend_with_pullbacks()), _cm, 1).verdict
        v_chop = _gate.run(BacktestResult(trades_r=choppy_ranging()), _cm, 1).verdict
        assert v_trend == "ROBUST"
        assert v_chop == "FRAGILE"

    def test_is_oos_degradation_detectable(self):
        """Simulate IS tuned on trending data; OOS is choppy — regime shift."""
        is_trades = trend_with_pullbacks(n=100, win_rate=0.65, rr=2.5, seed=10)
        oos_trades = choppy_ranging(n=100, win_rate=0.52, rr=0.90, seed=11)

        is_pf = BacktestResult(trades_r=is_trades).profit_factor_gross
        oos_pf = BacktestResult(trades_r=oos_trades).profit_factor_gross

        # IS edge should be meaningfully larger than OOS under regime shift
        assert is_pf > oos_pf * 2.0

    def test_regime_shift_shows_in_walk_forward_pf_spread(self):
        """First-half (IS) strong, second-half (OOS) weak reflects regime shift."""
        is_trades = trend_with_pullbacks(n=100, win_rate=0.65, rr=2.5, seed=7)
        oos_trades = choppy_ranging(n=100, win_rate=0.52, rr=0.90, seed=8)

        is_r = BacktestResult(trades_r=is_trades)
        oos_r = BacktestResult(trades_r=oos_trades)

        is_expectancy = is_r.expectancy_r
        oos_expectancy = oos_r.expectancy_r

        assert is_expectancy > 0
        assert oos_expectancy < 0  # negative expectancy in choppy regime
