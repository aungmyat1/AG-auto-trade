"""CME futures contract roll reference for IB data.

Primary path: IBHistoricalLoader uses secType='CONTFUT', which has IB handle
the roll automatically. This module exists for:
  - Documentation of CME expiry schedules (for logging / auditing roll dates)
  - get_front_month() helper when you need a specific contract symbol
    (e.g. "GCZ25", "6EH26") rather than the continuous series

CME Expiry Rules (simplified):
  GC/MGC (Gold):  3rd-to-last business day of the delivery month
                  Delivery months: Feb, Apr, Jun, Aug, Oct, Dec
  6E (Euro FX):   3rd Wednesday of the contract month
                  Contract months: Mar, Jun, Sep, Dec
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

# IB month codes (same as CME)
_MONTH_CODE = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
               7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}

# Active delivery months per symbol
_DELIVERY_MONTHS: dict[str, tuple[int, ...]] = {
    "GC":  (2, 4, 6, 8, 10, 12),
    "MGC": (2, 4, 6, 8, 10, 12),
    "6E":  (3, 6, 9, 12),
}


def get_front_month(symbol: str, as_of: date | None = None) -> str:
    """Return the IB contract local-symbol for the front month on as_of date.

    Examples:
        get_front_month("GC",  date(2025, 11, 1)) → "GCZ25"
        get_front_month("6E",  date(2025, 10, 1)) → "6EZ25"
    """
    if as_of is None:
        as_of = date.today()

    months = _DELIVERY_MONTHS[symbol]
    for m in months:
        expiry = _expiry_date(symbol, as_of.year, m)
        if expiry > as_of:
            yr = str(expiry.year)[2:]
            return f"{symbol}{_MONTH_CODE[m]}{yr}"

    # Roll into first delivery month of next year
    m = months[0]
    expiry = _expiry_date(symbol, as_of.year + 1, m)
    yr = str(expiry.year)[2:]
    return f"{symbol}{_MONTH_CODE[m]}{yr}"


def front_month_sequence(symbol: str, start: date, end: date) -> list[tuple[str, date, date]]:
    """Return list of (contract_symbol, valid_from, valid_until) for start→end range.

    Each entry covers the period when that contract is front-month (i.e. the
    period between the prior contract's last trading day and this contract's).
    """
    result = []
    current = start
    while current < end:
        front = get_front_month(symbol, current)
        m_code = front[-3]
        m_num = {v: k for k, v in _MONTH_CODE.items()}[m_code]
        yr = int("20" + front[-2:])
        roll = _expiry_date(symbol, yr, m_num)
        result.append((front, current, min(roll, end)))
        current = roll + timedelta(days=1)
    return result


# ── Expiry date helpers ───────────────────────────────────────────────────────

def _expiry_date(symbol: str, year: int, month: int) -> date:
    if symbol in ("GC", "MGC"):
        return _nth_to_last_business_day(year, month, n=3)
    if symbol == "6E":
        return _nth_weekday_of_month(year, month, weekday=2, n=3)  # Wednesday
    raise ValueError(f"No expiry rule for {symbol}")


def _nth_to_last_business_day(year: int, month: int, n: int) -> date:
    """Return the n-th to last business day (Mon–Fri) of the given month."""
    # Start from last day of month and walk backwards
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)

    count = 0
    d = last
    while True:
        if d.weekday() < 5:  # Mon–Fri
            count += 1
            if count == n:
                return d
        d -= timedelta(days=1)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Return the n-th occurrence of weekday (0=Mon … 6=Sun) in the given month."""
    d = date(year, month, 1)
    count = 0
    while True:
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)
