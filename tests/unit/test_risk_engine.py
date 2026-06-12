"""
Unit tests for RiskEngine — all 6 guards + state management.

G5 (leverage) is advisory and NOT enforced in validate_entry(), so there
is no direct validate_entry() test for G5 — see comment on G5 in engine.py.
"""
from __future__ import annotations

import time

import pytest

from ag.risk.engine import RiskEngine, RiskConfig, RiskDecision


# ── helpers ────────────────────────────────────────────────────────────────────

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


# ── default approval ───────────────────────────────────────────────────────────

class TestDefaultApproval:
    def test_fresh_engine_approves_standard_trade(self):
        engine = RiskEngine()
        result = engine.validate_entry(position_size_pct=0.005)
        assert result.approved is True
        assert result.violations == []

    def test_risk_decision_fields_populated(self):
        engine = RiskEngine()
        result = engine.validate_entry(0.005)
        assert isinstance(result, RiskDecision)
        assert isinstance(result.daily_pnl_pct, float)
        assert isinstance(result.current_drawdown_pct, float)
        assert isinstance(result.risk_score, float)
        assert isinstance(result.cooldown_remaining_s, int)

    def test_risk_score_zero_on_no_losses(self):
        engine = RiskEngine()
        result = engine.validate_entry(0.005)
        assert result.risk_score == pytest.approx(0.0)


# ── G1: daily loss ─────────────────────────────────────────────────────────────

class TestG1DailyLoss:
    def test_approves_below_daily_limit(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.019)
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_rejects_at_daily_limit(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.02)  # exactly at limit
        result = engine.validate_entry(0.005)
        assert result.approved is False
        assert any("G1" in v for v in result.violations)

    def test_rejects_over_daily_limit(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.025)
        result = engine.validate_entry(0.005)
        assert result.approved is False

    def test_risk_score_scales_with_daily_loss(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.01)   # 50% of limit used
        result = engine.validate_entry(0.005)
        assert result.risk_score == pytest.approx(50.0, abs=1.0)

    def test_reset_daily_clears_pnl(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.025)
        engine.reset_daily()
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_daily_pnl_reported_in_result(self):
        engine = _engine(daily_loss=0.02)
        engine.record_trade_result(-0.015)
        result = engine.validate_entry(0.005)
        assert result.daily_pnl_pct == pytest.approx(-0.015, rel=1e-6)


# ── G2: max drawdown ───────────────────────────────────────────────────────────
# Use daily_loss=0.99 to isolate G2 from G1 when testing large pnl losses.

class TestG2MaxDrawdown:
    def test_approves_below_drawdown_limit(self):
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(-0.14)
        result = engine.validate_entry(0.005)
        # drawdown on balance: (1.0 - 0.86) / 1.0 = 14%, below 15%
        assert result.approved is True

    def test_rejects_at_drawdown_limit(self):
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(-0.15)  # balance → 0.85, DD = 15%
        result = engine.validate_entry(0.005)
        assert result.approved is False
        assert any("G2" in v for v in result.violations)

    def test_peak_resets_after_recovery(self):
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(-0.1)    # loss, peak stays 1.0
        engine.record_trade_result(0.15)    # recovery above 1.0, new peak
        result = engine.validate_entry(0.005)
        assert result.approved is True
        assert result.current_drawdown_pct == pytest.approx(0.0, abs=0.01)

    def test_drawdown_reported_in_result(self):
        engine = _engine(drawdown=0.15, daily_loss=0.99)
        engine.record_trade_result(-0.1)
        result = engine.validate_entry(0.005)
        # balance = 0.90, peak = 1.0, dd = 0.10
        assert result.current_drawdown_pct == pytest.approx(0.10, rel=1e-4)


# ── G3: cooldown ───────────────────────────────────────────────────────────────

class TestG3Cooldown:
    def test_no_cooldown_after_wins(self):
        engine = _engine(max_losses=3, cooldown_s=60)
        for _ in range(5):
            engine.record_trade_result(0.01)
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_cooldown_triggers_after_max_consecutive_losses(self):
        engine = _engine(max_losses=3, cooldown_s=3600)
        for _ in range(3):
            engine.record_trade_result(-0.005)
        result = engine.validate_entry(0.005)
        assert result.approved is False
        assert any("G3" in v for v in result.violations)
        assert result.cooldown_remaining_s > 0

    def test_one_win_resets_consecutive_losses(self):
        engine = _engine(max_losses=3, cooldown_s=3600)
        for _ in range(2):
            engine.record_trade_result(-0.005)
        engine.record_trade_result(0.01)    # win resets counter
        engine.record_trade_result(-0.005)  # only 1 loss now
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_cooldown_expires_allows_entry(self):
        engine = _engine(max_losses=3, cooldown_s=1)  # 1-second cooldown
        for _ in range(3):
            engine.record_trade_result(-0.005)
        time.sleep(1.1)  # wait for cooldown to expire
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_two_losses_below_threshold_no_cooldown(self):
        engine = _engine(max_losses=3, cooldown_s=3600)
        for _ in range(2):
            engine.record_trade_result(-0.005)
        result = engine.validate_entry(0.005)
        assert result.approved is True


# ── G4: position size ──────────────────────────────────────────────────────────

class TestG4PositionSize:
    def test_at_max_size_passes(self):
        engine = _engine(max_size=0.005)
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_over_max_size_rejects(self):
        engine = _engine(max_size=0.005)
        result = engine.validate_entry(0.006)
        assert result.approved is False
        assert any("G4" in v for v in result.violations)

    def test_well_below_max_size_passes(self):
        engine = _engine(max_size=0.01)
        result = engine.validate_entry(0.001)
        assert result.approved is True


# ── G5: leverage (advisory — not enforced in validate_entry) ───────────────────

class TestG5LeverageAdvisory:
    def test_validate_entry_does_not_check_leverage(self):
        # G5 is advisory; validate_entry() has no leverage parameter
        # Verify the method signature — this confirms G5 is out of the guard chain
        engine = RiskEngine()
        import inspect
        sig = inspect.signature(engine.validate_entry)
        assert "leverage" not in sig.parameters


# ── G6: concurrent positions ──────────────────────────────────────────────────

class TestG6ConcurrentPositions:
    def test_allows_up_to_max_positions(self):
        engine = _engine(max_positions=3)
        engine.open_position("t1")
        engine.open_position("t2")
        result = engine.validate_entry(0.005)
        assert result.approved is True  # 2 open, max=3

    def test_rejects_when_at_max_positions(self):
        engine = _engine(max_positions=3)
        for i in range(3):
            engine.open_position(f"t{i}")
        result = engine.validate_entry(0.005)
        assert result.approved is False
        assert any("G6" in v for v in result.violations)

    def test_closing_position_allows_new_entry(self):
        engine = _engine(max_positions=3)
        for i in range(3):
            engine.open_position(f"t{i}")
        engine.record_trade_result(0.01, trade_id="t0")  # closes t0
        result = engine.validate_entry(0.005)
        assert result.approved is True

    def test_open_position_without_close_stays_registered(self):
        engine = RiskEngine()
        engine.open_position("trade-abc")
        assert "trade-abc" in engine.open_positions


# ── multi-guard violations ────────────────────────────────────────────────────

class TestMultipleViolations:
    def test_multiple_guards_report_all_violations(self):
        engine = _engine(daily_loss=0.02, max_size=0.005, max_positions=3)
        engine.record_trade_result(-0.025)  # trips G1
        for i in range(3):
            engine.open_position(f"t{i}")   # trips G6
        result = engine.validate_entry(0.006)  # also trips G4
        assert result.approved is False
        violation_codes = [v[:2] for v in result.violations]
        assert "G1" in violation_codes
        assert "G4" in violation_codes
        assert "G6" in violation_codes


# ── RiskConfig defaults ────────────────────────────────────────────────────────

class TestRiskConfigDefaults:
    def test_default_config_matches_ag_plan(self):
        cfg = RiskConfig()
        assert cfg.max_daily_loss_pct == pytest.approx(0.02)
        assert cfg.max_drawdown_pct == pytest.approx(0.15)
        assert cfg.max_consecutive_losses == 3
        assert cfg.cooldown_period_seconds == 3600
        assert cfg.max_position_size_pct == pytest.approx(0.005)
        assert cfg.max_leverage == 5
        assert cfg.max_concurrent_positions == 3
        assert cfg.weekly_loss_stop_pct == pytest.approx(0.06)

    def test_custom_config_overrides(self):
        cfg = RiskConfig(max_daily_loss_pct=0.05, max_position_size_pct=0.01)
        engine = RiskEngine(cfg)
        assert engine.config.max_daily_loss_pct == pytest.approx(0.05)
        result = engine.validate_entry(0.01)  # custom max size
        assert result.approved is True
