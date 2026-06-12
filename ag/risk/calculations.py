"""
Risk calculation utilities — pure functions, no side effects.

All dollar amounts use Decimal to avoid binary float errors.
Adapted from auto-trade-system/app/risk/calculations.py.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
from typing import Union

Number = Union[Decimal, int, float, str]
_CENTS = Decimal("0.01")


def to_decimal(value: Number) -> Decimal:
    """Convert to Decimal safely. Floats go through str() to avoid binary drift."""
    if value is None:
        raise ValueError("Cannot convert None to Decimal")
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    else:
        d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError(f"Non-finite value: {value!r}")
    return d


def calculate_position_size(
    account_balance: Number,
    risk_per_trade_pct: Number,
    entry_price: Number,
    stop_loss_price: Number,
    max_risk_pct: float = 0.005,
) -> dict:
    """
    Position size = (balance * risk%) / |entry - stop|

    All money math in Decimal. Returns quantity in units (not lots).
    """
    balance = to_decimal(account_balance)
    risk_pct = to_decimal(min(float(risk_per_trade_pct), max_risk_pct))
    entry = to_decimal(entry_price)
    stop = to_decimal(stop_loss_price)

    if entry <= 0 or stop <= 0:
        raise ValueError("Prices must be positive")
    if entry == stop:
        raise ValueError("Entry cannot equal stop loss")

    risk_amount = balance * risk_pct
    risk_per_unit = abs(entry - stop)
    quantity = risk_amount / risk_per_unit

    return {
        "quantity": quantity,
        "risk_amount": risk_amount.quantize(_CENTS, rounding=ROUND_HALF_EVEN),
        "risk_per_unit": risk_per_unit.quantize(_CENTS, rounding=ROUND_HALF_EVEN),
        "effective_risk_pct": float(risk_pct),
    }


def calculate_realized_pnl(
    side: str,
    entry_price: Number,
    exit_price: Number,
    quantity: Number,
    fees: Number = 0,
) -> dict:
    """Compute realized P&L — Decimal end-to-end."""
    entry = to_decimal(entry_price)
    exit_ = to_decimal(exit_price)
    qty = to_decimal(quantity)
    fee = to_decimal(fees)

    side_norm = (side or "").upper()
    if side_norm in ("LONG", "BUY"):
        gross = (exit_ - entry) * qty
    elif side_norm in ("SHORT", "SELL"):
        gross = (entry - exit_) * qty
    else:
        raise ValueError(f"Unknown side: {side!r}")

    profit = gross - fee
    position_value = entry * qty
    profit_pct = (profit / position_value * 100) if position_value > 0 else Decimal("0")

    return {
        "profit": profit.quantize(_CENTS, rounding=ROUND_HALF_EVEN),
        "profit_pct": profit_pct,
    }


def calculate_drawdown(current_balance: float, peak_balance: float) -> float:
    if peak_balance <= 0:
        return 0.0
    return max((peak_balance - current_balance) / peak_balance, 0.0)
