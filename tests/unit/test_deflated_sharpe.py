"""Unit tests for Deflated Sharpe Ratio."""
import pytest
import math
from ag.validation.deflated_sharpe import expected_max_sr, deflated_sharpe_z


class TestExpectedMaxSR:
    def test_zero_for_single_trial(self):
        assert expected_max_sr(1) == 0.0

    def test_increases_with_trials(self):
        sr1 = expected_max_sr(1)
        sr5 = expected_max_sr(5)
        sr15 = expected_max_sr(15)
        assert sr5 > sr1
        assert sr15 > sr5

    def test_positive_for_many_trials(self):
        assert expected_max_sr(10) > 0
        assert expected_max_sr(100) > 0


class TestDeflatedSharpeZ:
    def test_strong_edge_passes_gate(self):
        # 300 trades, consistent 2:1 RR at 55% win rate → strong SR
        import random
        random.seed(42)
        trades = [2.0 if random.random() < 0.55 else -1.0 for _ in range(300)]
        z = deflated_sharpe_z(trades, n_trials=1)
        assert z > 0, f"Expected z > 0, got {z:.4f}"

    def test_weak_edge_fails_with_high_trial_count(self):
        # Marginal edge + many trials tried = fails
        import random
        random.seed(42)
        trades = [1.1 if random.random() < 0.51 else -1.0 for _ in range(150)]
        z_low = deflated_sharpe_z(trades, n_trials=1)
        z_high = deflated_sharpe_z(trades, n_trials=20)
        assert z_high < z_low, "More trials should reduce z-score"

    def test_returns_zero_for_tiny_sample(self):
        assert deflated_sharpe_z([1.0, -1.0], n_trials=1) == 0.0

    def test_negative_edge_fails(self):
        # Losing strategy
        trades = [-1.0] * 200
        z = deflated_sharpe_z(trades, n_trials=1)
        assert z < 0

    def test_more_trials_requires_higher_sr(self):
        import random
        random.seed(0)
        trades = [1.5 if random.random() < 0.52 else -1.0 for _ in range(300)]
        z_1 = deflated_sharpe_z(trades, n_trials=1)
        z_15 = deflated_sharpe_z(trades, n_trials=15)
        # Same trades, same SR, but more trials means lower z
        assert z_1 > z_15
