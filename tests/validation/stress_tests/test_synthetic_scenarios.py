"""Gate stress tests using synthetic trade scenarios.

Each scenario has a pre-computed expected verdict based on the locked
gate thresholds (GATE_DECISION.md).  Do NOT modify gate thresholds to
make these tests pass — if a scenario gives the wrong verdict, the
scenario parameters need fixing.
"""
from __future__ import annotations

from ag.validation.gate import ValidationGate
from ag.validation.metrics import BacktestResult
from ag.validation.cost_model import CostModel
from .synthetic import (
    choppy_ranging,
    failed_breakout_inducement,
    liquidity_grab_reversal,
    news_spike_reversion,
    trend_with_pullbacks,
)

_gate = ValidationGate()
_cm = CostModel()     # default 0.15R — conservative baseline for tests


def _run(trades: list, n_trials: int = 1) -> str:
    return _gate.run(BacktestResult(trades_r=trades), _cm, n_trials).verdict


# ── Gate verdict per scenario ─────────────────────────────────────────────────

class TestScenarioVerdicts:
    def test_trend_robust(self):
        assert _run(trend_with_pullbacks()) == "ROBUST"

    def test_choppy_fragile(self):
        assert _run(choppy_ranging()) == "FRAGILE"

    def test_liquidity_grab_read(self):
        # n=150 passes floor (n≥50, gross PF>1) but fails ROBUST n≥200
        assert _run(liquidity_grab_reversal()) == "READ"

    def test_failed_breakout_fragile(self):
        assert _run(failed_breakout_inducement()) == "FRAGILE"

    def test_news_spike_fragile_low_count(self):
        # n=45 fails READ floor (n<50)
        assert _run(news_spike_reversion()) == "FRAGILE"


# ── New informational metrics populated correctly ─────────────────────────────

class TestNewMetrics:
    def test_calmar_positive_for_strong_strategy(self):
        assert BacktestResult(trades_r=trend_with_pullbacks()).calmar_ratio > 0.0

    def test_recovery_factor_positive_for_strong_strategy(self):
        assert BacktestResult(trades_r=trend_with_pullbacks()).recovery_factor > 0.0

    def test_max_consecutive_losses_is_nonneg_int(self):
        result = BacktestResult(trades_r=trend_with_pullbacks())
        mcl = result.max_consecutive_losses
        assert isinstance(mcl, int) and mcl >= 0

    def test_time_in_drawdown_in_unit_range(self):
        result = BacktestResult(trades_r=trend_with_pullbacks())
        assert 0.0 <= result.time_in_drawdown_pct <= 1.0

    def test_calmar_zero_when_no_drawdown(self):
        result = BacktestResult(trades_r=[1.0] * 50)
        # All wins → equity only goes up → max_drawdown = 0 → calmar = 0
        assert result.calmar_ratio == 0.0

    def test_recovery_zero_when_no_drawdown(self):
        result = BacktestResult(trades_r=[1.0] * 50)
        assert result.recovery_factor == 0.0

    def test_strong_has_fewer_consecutive_losses_than_choppy(self):
        strong = BacktestResult(trades_r=trend_with_pullbacks())
        choppy = BacktestResult(trades_r=choppy_ranging())
        assert strong.max_consecutive_losses <= choppy.max_consecutive_losses

    def test_strong_less_time_in_drawdown_than_choppy(self):
        strong = BacktestResult(trades_r=trend_with_pullbacks())
        choppy = BacktestResult(trades_r=choppy_ranging())
        assert strong.time_in_drawdown_pct < choppy.time_in_drawdown_pct
