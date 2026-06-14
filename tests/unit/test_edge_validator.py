"""Tests for EdgeValidator — baseline comparison (permutation test)."""
from __future__ import annotations

import random

import pytest

from ag.validation.edge_validator import EdgeValidator, EdgeResult, _profit_factor


def _make_trades(n: int, win_rate: float, avg_win_r: float, avg_loss_r: float, seed: int = 0) -> list:
    rng = random.Random(seed)
    trades = []
    for _ in range(n):
        if rng.random() < win_rate:
            trades.append(avg_win_r * (0.8 + rng.random() * 0.4))
        else:
            trades.append(-avg_loss_r * (0.8 + rng.random() * 0.4))
    return trades


class TestEdgeValidatorPass:
    """Cases that should PASS (strong edge above random)."""

    def test_strong_edge_passes(self):
        # PF ~2.0 system with 55% win rate — should easily beat random by 10%
        trades = _make_trades(300, win_rate=0.55, avg_win_r=2.0, avg_loss_r=1.0, seed=1)
        result = EdgeValidator().validate(trades)
        assert result.passed, result.report()
        assert result.outperformance_pct >= 0.10

    def test_outperformance_is_measured_relative_to_random(self):
        # Random permutation median PF should be ~1.0 for balanced trades
        trades = _make_trades(200, win_rate=0.60, avg_win_r=1.5, avg_loss_r=1.0, seed=2)
        result = EdgeValidator().validate(trades)
        assert result.random_baseline_pf > 0
        assert result.alpha_pf > result.random_baseline_pf

    def test_p_value_low_for_strong_edge(self):
        trades = _make_trades(500, win_rate=0.60, avg_win_r=2.0, avg_loss_r=1.0, seed=3)
        result = EdgeValidator().validate(trades)
        assert result.random_p_value < 0.05


class TestEdgeValidatorFail:
    """Cases that should FAIL (no real edge)."""

    def test_random_trades_fail(self):
        # 50% win rate, 1:1 R — pure noise
        trades = _make_trades(200, win_rate=0.50, avg_win_r=1.0, avg_loss_r=1.0, seed=4)
        result = EdgeValidator().validate(trades)
        assert not result.passed

    def test_negative_edge_fails(self):
        trades = _make_trades(200, win_rate=0.40, avg_win_r=0.9, avg_loss_r=1.0, seed=5)
        result = EdgeValidator().validate(trades)
        assert not result.passed
        assert result.outperformance_pct < 0.10

    def test_too_few_trades_fails(self):
        trades = _make_trades(30, win_rate=0.80, avg_win_r=3.0, avg_loss_r=1.0, seed=6)
        result = EdgeValidator().validate(trades)
        assert not result.passed
        assert any("insufficient" in d for d in result.details)


class TestEdgeValidatorReport:
    """Report and metadata correctness."""

    def test_report_contains_all_fields(self):
        trades = _make_trades(150, win_rate=0.55, avg_win_r=2.0, avg_loss_r=1.0, seed=7)
        result = EdgeValidator().validate(trades)
        report = result.report()
        assert "alpha PF" in report
        assert "random median PF" in report
        assert "outperformance" in report
        assert "p-value" in report

    def test_n_trades_matches_input(self):
        trades = _make_trades(123, win_rate=0.55, avg_win_r=1.5, avg_loss_r=1.0, seed=8)
        result = EdgeValidator().validate(trades)
        assert result.n_trades == 123

    def test_deterministic_with_same_seed(self):
        trades = _make_trades(200, win_rate=0.55, avg_win_r=1.5, avg_loss_r=1.0, seed=9)
        r1 = EdgeValidator().validate(trades)
        r2 = EdgeValidator().validate(trades)
        assert r1.random_baseline_pf == r2.random_baseline_pf
        assert r1.random_p_value == r2.random_p_value


class TestProfitFactor:
    """Utility function correctness."""

    def test_all_wins(self):
        assert _profit_factor([1.0, 2.0, 3.0]) == float("inf")

    def test_all_losses(self):
        pf = _profit_factor([-1.0, -2.0])
        assert pf == 0.0 or pf < 0.01

    def test_balanced(self):
        pf = _profit_factor([1.0, -1.0])
        assert pf == pytest.approx(1.0)

    def test_two_to_one(self):
        pf = _profit_factor([2.0, -1.0])
        assert pf == pytest.approx(2.0)
