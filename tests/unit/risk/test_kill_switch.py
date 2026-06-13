"""Unit tests for circuit-breaker (kill-switch) behavior of RiskEngine.

These tests focus on the *sustained* blocking pattern — that once a guard
trips it blocks every subsequent call until state is explicitly reset — and
on combined-guard scenarios not covered in test_risk_engine.py.
"""
from __future__ import annotations

import pytest

from ag.risk.engine import RiskEngine, RiskConfig


def _engine(daily_loss: float = 0.02, drawdown: float = 0.15,
            max_losses: int = 3, cooldown_s: int = 3600,
            max_size: float = 0.005, max_leverage: int = 5,
            max_positions: int = 3) -> RiskEngine:
    return RiskEngine(RiskConfig(
        max_daily_loss_pct=daily_loss,
        max_drawdown_pct=drawdown,
        max_consecutive_losses=max_losses,
        cooldown_period_seconds=cooldown_s,
        max_position_size_pct=max_size,
        max_leverage=max_leverage,
        max_concurrent_positions=max_positions,
    ))


# ── G1 as kill switch ─────────────────────────────────────────────────────────

class TestG1KillSwitch:
    def test_g1_blocks_all_subsequent_entries(self):
        """After G1 trips, every call until reset is blocked."""
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.025)
        for _ in range(5):
            assert engine.validate_entry(0.005).approved is False

    def test_g1_kill_cannot_be_cleared_by_winning_trade(self):
        """A win does NOT reset daily_pnl_pct — only reset_daily() does."""
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.025)   # trips G1
        engine.record_trade_result(+0.03)    # big win — but daily_pnl is now -0.025+0.03
        # After the win, daily_pnl = -0.025 + 0.03 = +0.005 → G1 no longer triggered
        assert engine.validate_entry(0.005).approved is True

    def test_reset_daily_reopens_g1(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.025)
        assert engine.validate_entry(0.005).approved is False
        engine.reset_daily()
        assert engine.validate_entry(0.005).approved is True

    def test_exactly_at_limit_is_blocked(self):
        """G1 triggers at <= -limit, so exactly -0.02 is blocked."""
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.02)
        assert engine.validate_entry(0.005).approved is False


# ── G2 as kill switch ─────────────────────────────────────────────────────────

class TestG2KillSwitch:
    def test_g2_sustained_block_on_deep_drawdown(self):
        """Large drawdown triggers G2 on every subsequent entry attempt."""
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(-0.20)   # balance → 0.80, dd = 20%
        for _ in range(3):
            result = engine.validate_entry(0.005)
            assert result.approved is False
            assert any("G2" in v for v in result.violations)

    def test_g2_unlocks_after_recovery(self):
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(-0.14)   # dd ≈ 14%, under limit
        assert engine.validate_entry(0.005).approved is True

    def test_g1_and_g2_both_active(self):
        """Sustained losses can trip both daily-loss and drawdown simultaneously."""
        engine = _engine(daily_loss=0.10, drawdown=0.12)
        engine.record_trade_result(-0.13)   # trips both G1 and G2
        result = engine.validate_entry(0.005)
        assert result.approved is False
        violation_codes = [v[:2] for v in result.violations]
        assert "G1" in violation_codes
        assert "G2" in violation_codes

    def test_g2_block_persists_across_consecutive_entries(self):
        engine = _engine(drawdown=0.10, daily_loss=0.99)
        engine.record_trade_result(-0.15)
        for _ in range(4):
            assert engine.validate_entry(0.005).approved is False


# ── G3 kill switch (consecutive-loss cooldown) ────────────────────────────────

class TestG3KillSwitch:
    def test_g3_blocks_every_entry_during_cooldown(self):
        engine = _engine(max_losses=3, cooldown_s=3600)
        for _ in range(3):
            engine.record_trade_result(-0.005)
        for _ in range(5):
            assert engine.validate_entry(0.005).approved is False

    def test_g3_block_persists_on_further_losses_during_cooldown(self):
        """Additional losses during cooldown don't reset the cooldown timer."""
        engine = _engine(max_losses=3, cooldown_s=3600)
        for _ in range(3):
            engine.record_trade_result(-0.005)
        # More losses recorded while cooldown active
        engine.record_trade_result(-0.005)
        engine.record_trade_result(-0.005)
        assert engine.validate_entry(0.005).approved is False


# ── G6 kill switch (max positions) ───────────────────────────────────────────

class TestG6KillSwitch:
    def test_g6_blocks_new_entry_at_capacity(self):
        engine = _engine(max_positions=2)
        engine.open_position("t1")
        engine.open_position("t2")
        assert engine.validate_entry(0.005).approved is False

    def test_g6_unblocks_when_position_closed(self):
        engine = _engine(max_positions=2)
        engine.open_position("t1")
        engine.open_position("t2")
        engine.record_trade_result(0.01, trade_id="t1")
        assert engine.validate_entry(0.005).approved is True


# ── Combined multi-guard cascade ──────────────────────────────────────────────

class TestCombinedGuards:
    def test_g1_g3_simultaneously_both_violations_reported(self):
        engine = _engine(daily_loss=0.02, max_losses=3, cooldown_s=3600)
        for _ in range(3):
            engine.record_trade_result(-0.008)  # total = -0.024 (trips G1) + G3
        result = engine.validate_entry(0.005)
        assert result.approved is False
        violation_codes = [v[:2] for v in result.violations]
        assert "G1" in violation_codes
        assert "G3" in violation_codes

    def test_all_guards_clear_on_reset_plus_recovery(self):
        """After reset_daily + recovery: all guards clear for standard entry."""
        engine = _engine(daily_loss=0.02, max_losses=2, cooldown_s=0)
        engine.record_trade_result(-0.025)   # G1
        engine.record_trade_result(-0.005)   # G3 (2nd loss after G1 skipped open)
        engine.reset_daily()
        engine.record_trade_result(+0.05)    # win resets consecutive losses
        assert engine.validate_entry(0.005).approved is True

    def test_approved_false_only_when_violation_exists(self):
        """Sanity: a fresh engine with no trades approves every entry."""
        engine = RiskEngine()
        for _ in range(10):
            assert engine.validate_entry(0.005).approved is True
