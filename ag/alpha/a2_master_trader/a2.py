"""
A2 — Master Trader Copy alpha module.

Gate verdict: READ (not ROBUST). See docs/validation/A2_GATE_RESULT.md.
is_ready() returns False until a ROBUST verdict is obtained.

generate_signal() replays the selected master's open positions.
A trade is considered "open" for the copy system at:
  open_time_ms + COPY_LAG_SECONDS × 1000 ≤ context_ts < close_time_ms
"""
from __future__ import annotations

from typing import Optional

from ag.alpha.base import AlphaModule, SignalProposal


# Locked per A2_MASTER_TRADER_DECISION.md §3
COPY_LAG_SECONDS: int = 30


class A2MasterTrader(AlphaModule):
    """
    Signal source: replay of master trader 279689 (TradingBridgeGold).
    Gate verdict: READ — contributes to A3 ensemble, not standalone entry.
    """

    alpha_id = "A2"
    description = "Master-trader copy (SignalStart, TradingBridgeGold 279689) — gate: READ"

    def __init__(self, open_trades: list[dict] | None = None) -> None:
        """
        Args:
            open_trades: list of dicts with keys open_time_ms, close_time_ms,
                         side ('BUY'/'SELL'), entry_price, exit_price.
                         If None, signal always returns None (no data loaded).
        """
        self._open_trades: list[dict] = open_trades or []

    def propose(self, market_data: dict) -> Optional[SignalProposal]:
        """
        Return a signal if the selected master has an open position at the
        given context timestamp.

        market_data expected keys:
          timestamp_ms (int) — current time as millisecond epoch
          price (float)      — current mid-price

        Returns None if no open master trade at this timestamp.
        """
        ts_ms: int = market_data.get("timestamp_ms", 0)
        price: float = market_data.get("price", 0.0)

        for trade in self._open_trades:
            copy_open_ms = trade["open_time_ms"] + COPY_LAG_SECONDS * 1000
            if copy_open_ms <= ts_ms < trade["close_time_ms"]:
                direction = "long" if trade["side"].upper() == "BUY" else "short"
                return SignalProposal(
                    direction=direction,
                    confidence=0.77,  # master's historical WR
                    alpha_id=self.alpha_id,
                    entry_rationale=f"copy master 279689 {trade['side']} @ {trade['entry_price']:.2f}",
                    stop_distance_pct=0.005,
                    target_distance_pct=0.006,
                    instrument="XAUUSD",
                    timeframe="copy",
                )
        return None

    def is_ready(self) -> bool:
        """Gate verdict is READ, not ROBUST. Not cleared for live deployment."""
        return False
