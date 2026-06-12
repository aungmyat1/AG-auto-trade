"""
Load SignalStart master-trader trades for A2.

Selection rule is locked in:
  ag/validation/lock_before_look/A2_MASTER_TRADER_DECISION.md

Selected master: 279689 (TradingBridgeGold Forex Signals)
  Tier A, n=525, PF=4.19, DD=4.4%, WR=77%, 430 trading days
IS/OOS split: first IS_N=200 trades (chronological) = IS; remainder = OOS
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


# Locked per A2_MASTER_TRADER_DECISION.md §7
SELECTED_UID: str = "279689"
IS_N: int = 200  # IS trades count (fixed; changing = +1 trial)

# XAUUSD pip conventions (declared assumption per §2 of the decision doc)
PIP_SIZE_USD: float = 0.10  # 1 pip = $0.10/oz (MT4/MT5 standard for gold)
COPY_LAG_PIPS: float = 1.5   # total round-trip cost: 0.5 slip entry + 0.5 exit + 0.5 commission each


class RawTrade(NamedTuple):
    entry_price: float
    exit_price: float
    side: str        # 'BUY' or 'SELL'
    open_time_dt: str
    close_time_dt: str
    hold_hours: float


@dataclass
class SplitResult:
    is_trades: list[RawTrade]
    oos_trades: list[RawTrade]
    is_cutoff_dt: str
    oos_start_dt: str
    trader_uid: str
    total_n: int


def load_master_trades(db_path: str | Path, uid: str = SELECTED_UID) -> list[RawTrade]:
    """
    Load all trades for the given master UID from the SignalStart DB,
    sorted chronologically by open_time_ms.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entry_price, exit_price, side, open_time_dt, close_time_dt, hold_hours
            FROM trades
            WHERE trader_mark = ?
            ORDER BY open_time_ms ASC
            """,
            (uid,),
        )
        return [RawTrade(*row) for row in cursor.fetchall()]
    finally:
        conn.close()


def split_is_oos(trades: list[RawTrade], is_n: int = IS_N) -> SplitResult:
    """
    Temporal IS/OOS split: first is_n trades = IS, remainder = OOS.
    The split point is determined by trade count (not calendar date),
    so the IS_CUTOFF is the open_time_dt of trade #is_n (index is_n-1).
    """
    if len(trades) < is_n + 1:
        raise ValueError(
            f"Insufficient trades for IS/OOS split: need >{is_n}, got {len(trades)}"
        )
    is_trades = trades[:is_n]
    oos_trades = trades[is_n:]
    return SplitResult(
        is_trades=is_trades,
        oos_trades=oos_trades,
        is_cutoff_dt=is_trades[-1].open_time_dt,
        oos_start_dt=oos_trades[0].open_time_dt,
        trader_uid=SELECTED_UID,
        total_n=len(trades),
    )
