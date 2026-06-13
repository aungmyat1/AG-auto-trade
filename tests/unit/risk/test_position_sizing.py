"""Unit tests for ag.risk.calculations — pure position-sizing functions.

These test the Decimal-based maths in isolation; engine state tests live in
test_risk_engine.py.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from ag.risk.calculations import (
    calculate_position_size,
    calculate_realized_pnl,
    calculate_drawdown,
    to_decimal,
)


# ── to_decimal ────────────────────────────────────────────────────────────────

class TestToDecimal:
    def test_int_converts(self):
        assert to_decimal(100) == Decimal("100")

    def test_float_goes_through_str(self):
        # 0.1 + 0.2 in float is not exactly 0.3, but str() round-trips cleanly
        d = to_decimal(0.1)
        assert str(d) == "0.1"

    def test_decimal_passthrough(self):
        v = Decimal("3.14159")
        assert to_decimal(v) is v

    def test_string_input(self):
        assert to_decimal("99.5") == Decimal("99.5")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            to_decimal(None)

    def test_inf_raises(self):
        with pytest.raises(ValueError):
            to_decimal(float("inf"))

    def test_nan_raises(self):
        with pytest.raises(ValueError):
            to_decimal(float("nan"))


# ── calculate_position_size ───────────────────────────────────────────────────

class TestCalculatePositionSize:
    def test_basic_long_sizing(self):
        """balance=$10k, risk 0.5%, entry=100, stop=99 → qty=50 units."""
        result = calculate_position_size(
            account_balance=10_000,
            risk_per_trade_pct=0.005,
            entry_price=100,
            stop_loss_price=99,
        )
        # risk_amount = 10000 * 0.005 = 50
        # risk_per_unit = |100 - 99| = 1
        # quantity = 50 / 1 = 50
        assert result["quantity"] == pytest.approx(Decimal("50"), rel=1e-6)

    def test_risk_amount_correct(self):
        result = calculate_position_size(10_000, 0.005, 100, 99)
        assert result["risk_amount"] == Decimal("50.00")

    def test_risk_per_unit_correct(self):
        result = calculate_position_size(10_000, 0.005, 100, 98)
        assert result["risk_per_unit"] == Decimal("2.00")
        assert result["quantity"] == pytest.approx(Decimal("25"), rel=1e-6)

    def test_max_risk_pct_clamps_oversized_request(self):
        """Requesting 2% risk is clamped to the 0.5% cap."""
        result = calculate_position_size(
            account_balance=10_000,
            risk_per_trade_pct=0.02,   # asks for 2%
            entry_price=100,
            stop_loss_price=99,
            max_risk_pct=0.005,        # cap at 0.5%
        )
        assert result["effective_risk_pct"] == pytest.approx(0.005)

    def test_effective_risk_pct_preserved_when_under_cap(self):
        result = calculate_position_size(10_000, 0.003, 100, 99, max_risk_pct=0.005)
        assert result["effective_risk_pct"] == pytest.approx(0.003)

    def test_short_stop_above_entry(self):
        """For a short, stop_loss > entry — function handles either order."""
        result = calculate_position_size(10_000, 0.005, 99, 100)
        assert result["risk_per_unit"] == Decimal("1.00")
        assert result["quantity"] == pytest.approx(Decimal("50"), rel=1e-6)

    def test_entry_equals_stop_raises(self):
        with pytest.raises(ValueError, match="Entry cannot equal stop"):
            calculate_position_size(10_000, 0.005, 100, 100)

    def test_zero_entry_raises(self):
        with pytest.raises(ValueError, match="Prices must be positive"):
            calculate_position_size(10_000, 0.005, 0, 99)

    def test_negative_stop_raises(self):
        with pytest.raises(ValueError, match="Prices must be positive"):
            calculate_position_size(10_000, 0.005, 100, -1)

    def test_returns_dict_with_all_keys(self):
        result = calculate_position_size(10_000, 0.005, 100, 99)
        assert {"quantity", "risk_amount", "risk_per_unit", "effective_risk_pct"} <= result.keys()

    def test_decimal_precision_maintained(self):
        """Risk amount and risk_per_unit are quantized to cents."""
        result = calculate_position_size(10_000, 0.005, 100.33, 99.12)
        assert result["risk_amount"] == result["risk_amount"].quantize(Decimal("0.01"))
        assert result["risk_per_unit"] == result["risk_per_unit"].quantize(Decimal("0.01"))


# ── calculate_realized_pnl ────────────────────────────────────────────────────

class TestCalculateRealizedPnl:
    def test_long_win(self):
        result = calculate_realized_pnl("long", 100, 105, 10)
        assert result["profit"] == Decimal("50.00")

    def test_long_loss(self):
        result = calculate_realized_pnl("LONG", 100, 95, 10)
        assert result["profit"] == Decimal("-50.00")

    def test_short_win(self):
        result = calculate_realized_pnl("short", 100, 95, 10)
        assert result["profit"] == Decimal("50.00")

    def test_short_loss(self):
        result = calculate_realized_pnl("SHORT", 100, 105, 10)
        assert result["profit"] == Decimal("-50.00")

    def test_buy_alias(self):
        result = calculate_realized_pnl("BUY", 100, 110, 5)
        assert result["profit"] == Decimal("50.00")

    def test_sell_alias(self):
        result = calculate_realized_pnl("SELL", 100, 90, 5)
        assert result["profit"] == Decimal("50.00")

    def test_fees_deducted(self):
        result = calculate_realized_pnl("long", 100, 105, 10, fees=5)
        assert result["profit"] == Decimal("45.00")

    def test_profit_pct_populated(self):
        result = calculate_realized_pnl("long", 100, 105, 10)
        # gross = 50, position_value = 100*10 = 1000 → pct = 5%
        assert float(result["profit_pct"]) == pytest.approx(5.0, rel=1e-4)

    def test_breakeven_zero_profit(self):
        result = calculate_realized_pnl("long", 100, 100, 10)
        assert result["profit"] == Decimal("0.00")

    def test_unknown_side_raises(self):
        with pytest.raises(ValueError, match="Unknown side"):
            calculate_realized_pnl("hold", 100, 105, 10)


# ── calculate_drawdown ────────────────────────────────────────────────────────

class TestCalculateDrawdown:
    def test_no_drawdown_at_peak(self):
        assert calculate_drawdown(100.0, 100.0) == pytest.approx(0.0)

    def test_ten_percent_drawdown(self):
        assert calculate_drawdown(90.0, 100.0) == pytest.approx(0.10)

    def test_drawdown_clamped_at_zero(self):
        # current > peak (shouldn't normally happen, but function handles it)
        assert calculate_drawdown(110.0, 100.0) == pytest.approx(0.0)

    def test_zero_peak_returns_zero(self):
        assert calculate_drawdown(50.0, 0.0) == pytest.approx(0.0)

    def test_full_loss(self):
        assert calculate_drawdown(0.0, 100.0) == pytest.approx(1.0)
