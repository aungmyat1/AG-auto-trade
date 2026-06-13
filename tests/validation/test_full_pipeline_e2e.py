"""Offline end-to-end pipeline test: alpha → RiskEngine → harness → gate.

Proves the wiring of the full validation pipeline without any market data or
network: a deterministic stub alpha drives scripts/run_alpha_backtest.py's
run_backtest(), the risk engine sits non-bypassably in the loop, and the
resulting R-series flows through BacktestResult into ValidationGate.

This tests INFRASTRUCTURE only. It is not an alpha evaluation: the stub's
trades come from seeded random-walk bars, so no real strategy sees data and
no DSR trial is consumed.
"""
from __future__ import annotations

import importlib.util
import pathlib
from typing import Optional

import pytest

from ag.alpha.base import AlphaModule, SignalProposal
from ag.risk.engine import RiskConfig, RiskEngine
from ag.validation.cost_model import CostModel
from ag.validation.gate import ValidationGate
from ag.validation.metrics import BacktestResult

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load_harness():
    """Import scripts/run_alpha_backtest.py as a module (scripts/ is not a package)."""
    path = _REPO_ROOT / "scripts" / "run_alpha_backtest.py"
    spec = importlib.util.spec_from_file_location("run_alpha_backtest", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


harness = _load_harness()


class _EveryKBarsAlpha(AlphaModule):
    """Deterministic stub: proposes a 1%-stop / 2%-target long every k-th call."""

    alpha_id = "STUB"
    description = "deterministic test stub — not a strategy"

    def __init__(self, k: int = 4):
        self.k = k
        self._calls = 0

    def propose(self, market_data: dict) -> Optional[SignalProposal]:
        self._calls += 1
        if self._calls % self.k:
            return None
        return SignalProposal(
            direction="long",
            confidence=0.9,
            alpha_id=self.alpha_id,
            entry_rationale="stub signal (test fixture)",
            stop_distance_pct=1.0,
            target_distance_pct=2.0,
        )

    def is_ready(self) -> bool:
        return False


@pytest.fixture(scope="module")
def synthetic_df():
    df = harness._make_synthetic_df(500)
    assert df is not None, "pandas/numpy required"
    return df


@pytest.fixture
def trades(synthetic_df):
    return harness.run_backtest(
        _EveryKBarsAlpha(k=4), synthetic_df, RiskEngine(RiskConfig()), lookback=50
    )


class TestHarnessWiring:
    def test_signal_cadence_reaches_floor_n(self, trades):
        # 450 evaluated bars / every 4th → >= 100 proposals: above the READ floor (50)
        assert len(trades) >= 100

    def test_every_trade_carries_risk_decision_fields(self, trades):
        for t in trades:
            assert isinstance(t["risk_approved"], bool)
            assert "risk_violations" in t
            assert t["direction"] == "long"
            assert t["stop_pct"] == pytest.approx(0.01)

    def test_approved_trades_have_r_multiple(self, trades):
        approved = [t for t in trades if t["risk_approved"]]
        assert approved, "healthy engine should approve trades"
        for t in approved:
            assert isinstance(t["r_multiple"], float)

    def test_deterministic_given_seeded_data(self, synthetic_df):
        a = harness.run_backtest(
            _EveryKBarsAlpha(4), synthetic_df, RiskEngine(RiskConfig()), lookback=50
        )
        b = harness.run_backtest(
            _EveryKBarsAlpha(4), synthetic_df, RiskEngine(RiskConfig()), lookback=50
        )
        assert a == b


class TestRiskEngineIsInTheLoop:
    def test_tripped_daily_loss_blocks_every_entry(self, synthetic_df):
        engine = RiskEngine(RiskConfig())
        engine.daily_pnl_pct = -0.05  # beyond the 2% daily stop
        trades = harness.run_backtest(
            _EveryKBarsAlpha(4), synthetic_df, engine, lookback=50
        )
        assert trades, "stub still proposes; risk must be the one rejecting"
        assert all(t["risk_approved"] is False for t in trades)
        assert all("G1" in t["risk_violations"] for t in trades)
        assert all(t["r_multiple"] == 0.0 for t in trades)

    def test_oversized_request_blocked_by_g4(self, synthetic_df):
        engine = RiskEngine(RiskConfig(max_position_size_pct=0.001))
        trades = harness.run_backtest(
            _EveryKBarsAlpha(4), synthetic_df, engine, lookback=50
        )
        assert all(t["risk_approved"] is False for t in trades)
        assert all("G4" in t["risk_violations"] for t in trades)


class TestGateConsumesHarnessOutput:
    def test_harness_r_series_flows_through_gate(self, trades):
        r = [t["r_multiple"] for t in trades if t["risk_approved"]]
        result = ValidationGate().run(
            BacktestResult(trades_r=r, instrument="SYNTH", n_trials=1),
            CostModel(),
            n_trials=1,
        )
        assert result.verdict in ("ROBUST", "READ", "FRAGILE")
        assert result.n_trades == len(r)
        assert result.checks, "gate must report individual checks"

    def test_random_walk_noise_is_not_robust(self, trades):
        # Safety property: seeded noise through the stub must never clear ROBUST.
        r = [t["r_multiple"] for t in trades if t["risk_approved"]]
        result = ValidationGate().run(
            BacktestResult(trades_r=r, instrument="SYNTH", n_trials=1),
            CostModel(),
            n_trials=1,
        )
        assert result.verdict != "ROBUST"

    def test_real_a0_mvp_alpha_runs_through_harness(self, synthetic_df):
        # Smoke only: the real A0_MVP wiring executes end-to-end on synthetic
        # bars. No assertion on signal count/quality — that is Phase B work on
        # real GC data, and counting it here would be a fake alpha evaluation.
        alpha = harness._build_alpha("a0_mvp")
        out = harness.run_backtest(alpha, synthetic_df, RiskEngine(RiskConfig()))
        assert isinstance(out, list)
        assert alpha.is_ready() is False
