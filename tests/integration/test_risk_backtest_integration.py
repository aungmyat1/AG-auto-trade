"""Integration tests: RiskEngine through a full simulated backtest session.

Tests the multi-trade lifecycle — open → record → close — and verifies that
guards accumulate state correctly across a sequence of trades.
Unit-level guard tests live in tests/unit/test_risk_engine.py.
"""
from __future__ import annotations

import pytest

from ag.risk.engine import RiskEngine, RiskConfig


def _engine(
    daily_loss: float = 0.02,
    drawdown: float = 0.15,
    max_losses: int = 3,
    cooldown_s: int = 3600,
    max_size: float = 0.005,
    max_leverage: int = 5,
    max_positions: int = 3,
) -> RiskEngine:
    return RiskEngine(RiskConfig(
        max_daily_loss_pct=daily_loss,
        max_drawdown_pct=drawdown,
        max_consecutive_losses=max_losses,
        cooldown_period_seconds=cooldown_s,
        max_position_size_pct=max_size,
        max_leverage=max_leverage,
        max_concurrent_positions=max_positions,
    ))


# ── Trade lifecycle ───────────────────────────────────────────────────────────

class TestTradeCycle:
    def test_open_and_close_single_position(self):
        engine = RiskEngine()
        assert engine.validate_entry(0.005).approved is True
        engine.open_position("trade-1")
        assert "trade-1" in engine.open_positions
        engine.record_trade_result(+0.01, trade_id="trade-1")
        assert "trade-1" not in engine.open_positions

    def test_daily_pnl_accumulates_across_trades(self):
        # max_losses=10 so G3 cooldown doesn't fire on only 3 losses
        engine = _engine(daily_loss=0.05, max_losses=10, cooldown_s=3600)
        engine.open_position("t1")
        engine.record_trade_result(-0.01, trade_id="t1")
        engine.open_position("t2")
        engine.record_trade_result(-0.01, trade_id="t2")
        engine.open_position("t3")
        engine.record_trade_result(-0.01, trade_id="t3")
        result = engine.validate_entry(0.005)
        assert result.daily_pnl_pct == pytest.approx(-0.03, rel=1e-4)
        assert result.approved is True  # still under 5% limit

    def test_g1_trip_mid_session(self):
        """Session: two normal trades, then a loss that hits G1.

        Net pnl after the three trades: +0.01 - 0.005 - 0.03 = -0.025 <= -0.02 → G1.
        max_losses=10 keeps G3 from firing concurrently.
        """
        engine = _engine(daily_loss=0.02, max_losses=10, cooldown_s=3600)
        engine.open_position("t1")
        engine.record_trade_result(+0.01, trade_id="t1")   # win
        engine.open_position("t2")
        engine.record_trade_result(-0.005, trade_id="t2")  # small loss
        engine.open_position("t3")
        engine.record_trade_result(-0.03, trade_id="t3")   # trips G1 (net = -0.025)
        assert engine.validate_entry(0.005).approved is False

    def test_g6_position_count_is_accurate(self):
        engine = _engine(max_positions=3)
        engine.open_position("t1")
        engine.open_position("t2")
        assert len(engine.open_positions) == 2
        result = engine.validate_entry(0.005)
        assert result.approved is True  # 2 open, limit=3
        engine.open_position("t3")
        result = engine.validate_entry(0.005)
        assert result.approved is False  # now at 3

    def test_wins_do_not_increment_consecutive_losses(self):
        # max_losses=3; ensure daily_loss limit is high enough to not fire
        engine = _engine(max_losses=3, cooldown_s=3600, daily_loss=0.99)
        for _ in range(2):
            engine.record_trade_result(-0.005)  # 2 losses
        engine.record_trade_result(+0.01)       # win resets counter
        for _ in range(2):
            engine.record_trade_result(-0.005)  # 2 more losses (not 4)
        assert engine.validate_entry(0.005).approved is True  # counter=2 < threshold=3


# ── Daily session boundary ────────────────────────────────────────────────────

class TestDailyReset:
    def test_reset_daily_clears_pnl_and_allows_trading(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.025)   # trips G1
        engine.reset_daily()
        assert engine.validate_entry(0.005).approved is True

    def test_reset_daily_does_not_clear_drawdown(self):
        """reset_daily() only resets daily P&L — drawdown persists."""
        engine = _engine(daily_loss=0.99, drawdown=0.15)
        engine.record_trade_result(-0.20)   # trips G2 only (G1 limit is 99%)
        engine.reset_daily()
        result = engine.validate_entry(0.005)
        assert result.approved is False
        assert any("G2" in v for v in result.violations)

    def test_reset_daily_does_not_clear_open_positions(self):
        engine = _engine(max_positions=2)
        engine.open_position("t1")
        engine.open_position("t2")
        engine.reset_daily()
        assert len(engine.open_positions) == 2


# ── Multi-session simulation ──────────────────────────────────────────────────

class TestMultiSession:
    def test_three_day_simulation(self):
        """Simulate 3 trading days: G1 trips on day 2, resets for day 3."""
        engine = _engine(daily_loss=0.02, max_losses=10)

        # Day 1: normal trades
        engine.record_trade_result(+0.01)
        engine.record_trade_result(+0.01)
        engine.reset_daily()

        # Day 2: big loss trips G1
        engine.record_trade_result(-0.025)
        assert engine.validate_entry(0.005).approved is False
        engine.reset_daily()

        # Day 3: clean slate
        assert engine.validate_entry(0.005).approved is True

    def test_equity_curve_peak_survives_daily_reset(self):
        """Peak balance is NOT reset by reset_daily() — it tracks lifetime high."""
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(+0.10)    # peak → 1.10
        engine.reset_daily()
        engine.record_trade_result(-0.10)   # balance → 1.10 * 0.90 ≈ 0.99
        # drawdown from 1.10 = (1.10 - 0.99) / 1.10 ≈ 10%  (< 15%, should still pass)
        assert engine.validate_entry(0.005).approved is True

    def test_cumulative_drawdown_tracks_correctly(self):
        engine = _engine(drawdown=0.20, daily_loss=0.99)
        engine.record_trade_result(-0.10)   # balance = 0.90
        engine.reset_daily()
        engine.record_trade_result(-0.10)   # balance = 0.90 * 0.90 = 0.81
        result = engine.validate_entry(0.005)
        # DD = (1.0 - 0.81) / 1.0 = 19% < 20%
        assert result.current_drawdown_pct == pytest.approx(0.19, abs=0.01)
        assert result.approved is True


# ── Position metadata ─────────────────────────────────────────────────────────

class TestPositionMetadata:
    def test_open_position_stores_metadata(self):
        engine = RiskEngine()
        engine.open_position("t1", metadata={"direction": "long", "instrument": "GC"})
        assert engine.open_positions["t1"]["direction"] == "long"

    def test_closing_unknown_trade_id_does_not_crash(self):
        engine = RiskEngine()
        engine.record_trade_result(+0.01, trade_id="nonexistent")
        assert "nonexistent" not in engine.open_positions

    def test_closing_without_trade_id_does_not_affect_positions(self):
        engine = RiskEngine()
        engine.open_position("t1")
        engine.record_trade_result(+0.01)   # no trade_id
        assert "t1" in engine.open_positions   # still open
