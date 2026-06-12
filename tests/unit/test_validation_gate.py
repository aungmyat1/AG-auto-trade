"""Unit tests for the ValidationGate battery."""
from ag.validation import ValidationGate, BacktestResult, CostModel


def _make_trades(n_wins: int, n_losses: int, avg_win: float = 2.0, avg_loss: float = -1.0) -> list:
    import random
    trades = [avg_win] * n_wins + [avg_loss] * n_losses
    random.seed(42)
    random.shuffle(trades)
    return trades


class TestFloorChecks:
    def test_fragile_on_too_few_trades(self):
        result = BacktestResult(trades_r=_make_trades(20, 10))
        r = ValidationGate().run(result, CostModel(), n_trials=1)
        assert r.verdict == "FRAGILE"
        assert r.n_trades == 30

    def test_fragile_on_pf_below_1(self):
        # n=60 but PF < 1
        result = BacktestResult(trades_r=_make_trades(10, 50))
        r = ValidationGate().run(result, CostModel(), n_trials=1)
        assert r.verdict == "FRAGILE"

    def test_read_on_floor_pass(self):
        # n=60, PF > 1 but fails some ROBUST checks
        result = BacktestResult(trades_r=_make_trades(35, 25))
        r = ValidationGate().run(result, CostModel(), n_trials=1)
        assert r.verdict in ("READ", "ROBUST")
        assert r.n_trades == 60


class TestRobustChecks:
    def test_robust_on_strong_strategy(self):
        # 300 trades, 2:1 RR, 60% win rate → all checks should pass
        trades = _make_trades(180, 120, avg_win=2.0, avg_loss=-1.0)
        result = BacktestResult(trades_r=trades, n_trials=1)
        r = ValidationGate().run(result, CostModel(spread_r=0.02, commission_r=0.02, slippage_r=0.02), n_trials=1)
        assert r.verdict == "ROBUST", r.report()

    def test_read_on_marginal_pf(self):
        # PF just barely above 1 gross, fails net
        trades = _make_trades(55, 50, avg_win=1.05, avg_loss=-1.0)
        result = BacktestResult(trades_r=trades)
        r = ValidationGate().run(result, CostModel(), n_trials=1)
        # Cost will push PF net below 1.25
        assert r.verdict in ("READ", "FRAGILE")

    def test_n_threshold(self):
        gate = ValidationGate()
        assert gate.ROBUST_N == 200
        assert gate.READ_N == 50


class TestNetCost:
    def test_cost_reduces_pf(self):
        trades = _make_trades(60, 40, avg_win=2.0, avg_loss=-1.0)
        result = BacktestResult(trades_r=trades)
        no_cost = CostModel(0, 0, 0)
        with_cost = CostModel(0.1, 0.1, 0.1)
        r_no = ValidationGate().run(result, no_cost, n_trials=1)
        r_with = ValidationGate().run(result, with_cost, n_trials=1)
        pf_no = next(c.value for c in r_no.checks if "net PF" in c.name)
        pf_with = next(c.value for c in r_with.checks if "net PF" in c.name)
        assert pf_with < pf_no


class TestGateResultReport:
    def test_report_contains_verdict(self):
        result = BacktestResult(trades_r=_make_trades(25, 25))
        r = ValidationGate().run(result, CostModel(), n_trials=1)
        report = r.report()
        assert "VERDICT" in report
        assert r.verdict in report
