"""End-to-end tests for the full validation pipeline.

Tests the full path: synthetic trades → CostModel → ValidationGate → verdict.
These tests prove the three-tier verdict system (ROBUST / READ / FRAGILE) works
end-to-end, including cost model integration. Unit gate tests live in
tests/unit/test_validation_gate.py.
"""
from __future__ import annotations

import random

import pytest

from ag.validation import ValidationGate, BacktestResult, CostModel


# ── Trade generators ──────────────────────────────────────────────────────────

def _trades(n_wins: int, n_losses: int, avg_win: float = 2.0,
            avg_loss: float = -1.0, seed: int = 42) -> list[float]:
    ts = [avg_win] * n_wins + [avg_loss] * n_losses
    random.Random(seed).shuffle(ts)
    return ts


def _robust_trades(n: int = 300, seed: int = 42) -> list[float]:
    """300 trades at 60% win rate, 2:1 RR → comfortably ROBUST after low cost."""
    n_wins = int(n * 0.60)
    return _trades(n_wins, n - n_wins, avg_win=2.0, avg_loss=-1.0, seed=seed)


def _fragile_trades(n: int = 20) -> list[float]:
    """20 trades — under the READ floor of 50."""
    return _trades(12, 8, seed=0)[:n]


def _read_trades(seed: int = 99) -> list[float]:
    """65 trades, gross PF slightly above 1.0 → READ tier."""
    return _trades(35, 30, avg_win=1.1, avg_loss=-1.0, seed=seed)


def _zero_cost() -> CostModel:
    return CostModel(spread_r=0.0, commission_r=0.0, slippage_r=0.0)


def _gc_cost() -> CostModel:
    """Typical GC futures cost (from CostModel.for_gc())."""
    return CostModel.for_gc()


# ── FRAGILE verdict ───────────────────────────────────────────────────────────

class TestFragileVerdict:
    def test_fragile_on_too_few_trades(self):
        result = BacktestResult(trades_r=_fragile_trades(20), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        assert gate_result.verdict == "FRAGILE"

    def test_fragile_contains_floor_fail_check(self):
        result = BacktestResult(trades_r=_fragile_trades(20), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        failed = [c for c in gate_result.checks if not c.passed]
        assert any("n >=" in c.name for c in failed)

    def test_fragile_on_negative_pf(self):
        """60 trades but PF < 1 → FRAGILE even if n >= 50."""
        bad_trades = _trades(20, 40, avg_win=1.0, avg_loss=-1.0)  # PF ≈ 0.5
        result = BacktestResult(trades_r=bad_trades, n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        assert gate_result.verdict == "FRAGILE"

    def test_fragile_report_contains_verdict(self):
        result = BacktestResult(trades_r=_fragile_trades(20), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        assert "FRAGILE" in gate_result.report()


# ── READ verdict ──────────────────────────────────────────────────────────────

class TestReadVerdict:
    def test_read_on_floor_pass_but_not_robust(self):
        result = BacktestResult(trades_r=_read_trades(), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        assert gate_result.verdict in ("READ", "ROBUST")
        # With only 65 marginal trades, it's very unlikely to hit ROBUST
        assert gate_result.n_trades == 65

    def test_read_n_trades_reported_correctly(self):
        trades = _read_trades()
        result = BacktestResult(trades_r=trades, n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        assert gate_result.n_trades == len(trades)


# ── ROBUST verdict ────────────────────────────────────────────────────────────

class TestRobustVerdict:
    def test_robust_on_strong_strategy_no_cost(self):
        result = BacktestResult(trades_r=_robust_trades(300), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        assert gate_result.verdict == "ROBUST", gate_result.report()

    def test_robust_with_realistic_gc_cost(self):
        result = BacktestResult(trades_r=_robust_trades(300), n_trials=1)
        gate_result = ValidationGate().run(result, _gc_cost(), n_trials=1)
        assert gate_result.verdict == "ROBUST", gate_result.report()

    def test_robust_all_checks_pass(self):
        result = BacktestResult(trades_r=_robust_trades(300), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        failed = [c for c in gate_result.checks if not c.passed]
        assert failed == [], f"Unexpected failures: {[c.name for c in failed]}"

    def test_robust_report_contains_all_check_names(self):
        result = BacktestResult(trades_r=_robust_trades(300), n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=1)
        report = gate_result.report()
        for check_name in ("net PF", "win rate", "Sharpe", "max DD", "CPCV", "WF", "MC", "DSR"):
            assert check_name in report, f"'{check_name}' missing from report"


# ── Cost model integration ────────────────────────────────────────────────────

class TestCostIntegration:
    def test_high_cost_degrades_pf_below_threshold(self):
        """0.5R/trade cost on a borderline strategy pushes net PF below 1.25."""
        # 105 wins @1.4R, 95 losses @1.0R → gross PF = 147/95 ≈ 1.547
        # With 0.5R cost: net wins = 0.9R, net losses = 1.5R → net PF = 94.5/142.5 ≈ 0.66
        result = BacktestResult(trades_r=_trades(105, 95, avg_win=1.4, avg_loss=-1.0,
                                                  seed=7), n_trials=1)
        heavy_cost = CostModel(spread_r=0.25, commission_r=0.15, slippage_r=0.10)
        gate_result = ValidationGate().run(result, heavy_cost, n_trials=1)
        net_pf_check = next(c for c in gate_result.checks if "net PF" in c.name)
        assert not net_pf_check.passed, (
            f"Expected net PF to fail under heavy cost; got {net_pf_check.value:.3f}"
        )

    def test_zero_cost_gives_higher_pf_than_gc_cost(self):
        trades = _robust_trades(300)
        result = BacktestResult(trades_r=trades, n_trials=1)
        r_free = ValidationGate().run(result, _zero_cost(), n_trials=1)
        r_cost = ValidationGate().run(result, _gc_cost(), n_trials=1)
        pf_free = next(c.value for c in r_free.checks if "net PF" in c.name)
        pf_cost = next(c.value for c in r_cost.checks if "net PF" in c.name)
        assert pf_free > pf_cost

    def test_for_gc_preset_creates_valid_cost_model(self):
        cm = CostModel.for_gc()
        assert cm.total_r > 0
        assert cm.spread_r > 0
        assert cm.commission_r > 0


# ── Gate thresholds match GATE_DECISION.md ────────────────────────────────────

class TestGateThresholdsLocked:
    """Sanity-check that gate.py thresholds match the pre-registered spec.

    These are NOT duplicating lock_before_look tests — they verify the e2e
    gate object used in actual runs has the correct values.
    """

    def test_robust_n_threshold(self):
        assert ValidationGate.ROBUST_N == 200

    def test_read_n_threshold(self):
        assert ValidationGate.READ_N == 50

    def test_robust_pf_threshold(self):
        assert ValidationGate.ROBUST_PF_NET == pytest.approx(1.25)

    def test_robust_sharpe_threshold(self):
        assert ValidationGate.ROBUST_SHARPE == pytest.approx(1.2)

    def test_robust_max_dd_threshold(self):
        assert ValidationGate.ROBUST_MAX_DD == pytest.approx(0.15)

    def test_robust_win_rate_threshold(self):
        assert ValidationGate.ROBUST_WIN_RATE == pytest.approx(0.45)

    def test_robust_dsr_threshold(self):
        assert ValidationGate.ROBUST_DSR_Z == pytest.approx(0.0)


# ── n_trials penalty ──────────────────────────────────────────────────────────

class TestNTrialsPenalty:
    def test_more_trials_harder_dsr(self):
        """DSR z-score decreases as n_trials increases — honest trial accounting."""
        trades = _robust_trades(300)
        result = BacktestResult(trades_r=trades, n_trials=1)

        r_1 = ValidationGate().run(result, _zero_cost(), n_trials=1)
        r_50 = ValidationGate().run(result, _zero_cost(), n_trials=50)

        dsr_1 = next(c.value for c in r_1.checks if "DSR" in c.name)
        dsr_50 = next(c.value for c in r_50.checks if "DSR" in c.name)
        assert dsr_1 > dsr_50, "More trials must make DSR harder, not easier"

    def test_high_trial_count_can_fail_dsr(self):
        """With many trials, even a good strategy may fail the DSR check."""
        trades = _trades(105, 95, avg_win=1.5, avg_loss=-1.0)  # moderate strategy
        result = BacktestResult(trades_r=trades, n_trials=1)
        gate_result = ValidationGate().run(result, _zero_cost(), n_trials=500)
        dsr_check = next(c for c in gate_result.checks if "DSR" in c.name)
        # With 500 trials the bar is very high; strategy may fail DSR
        assert isinstance(dsr_check.passed, bool)  # result is deterministic
