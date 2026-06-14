"""Order Block (OB) detector.

Bullish OB: last bearish candle before a bullish displacement that breaks
the previous swing high.  Bearish OB: mirror.

Mitigation: OB is consumed when price closes through it
(bullish OB: close < OB.low; bearish OB: close > OB.high).

# ⚠️  FRAGILE — SMC as a standalone signal has no edge on GC H1 (see
# research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md).
# This module is a CONTEXT FILTER only: it answers WHERE (OB zones),
# never WHEN (entry timing).  Entry decisions live in AlphaModule.propose().
"""
from __future__ import annotations

from typing import List

import pandas as pd

from .base import OrderBlock, compute_atr


class OrderBlockDetector:
    def __init__(
        self,
        displacement_atr_mult: float = 1.5,
        atr_window: int = 14,
        lookback: int = 5,
    ) -> None:
        self.displacement_atr_mult = displacement_atr_mult
        self.atr_window = atr_window
        self.lookback = lookback

    def detect(self, df: pd.DataFrame) -> List[OrderBlock]:
        """Return all unmitigated OBs found in df."""
        min_bars = self.atr_window + self.lookback + 1
        if len(df) < min_bars:
            return []

        atr = compute_atr(df, self.atr_window)
        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        obs: List[OrderBlock] = []
        for i in range(self.lookback + 1, len(df)):
            body = abs(closes[i] - opens[i])
            atr_val = atr.iloc[i]
            if atr_val <= 0 or body < self.displacement_atr_mult * atr_val:
                continue

            bullish = closes[i] > opens[i]
            start = max(0, i - self.lookback)

            if bullish:
                if closes[i] <= max(highs[start:i]):
                    continue
                ob_idx = _last_opposing(closes, opens, start, i, bearish=True)
            else:
                if closes[i] >= min(lows[start:i]):
                    continue
                ob_idx = _last_opposing(closes, opens, start, i, bearish=False)

            if ob_idx is None:
                continue

            strength = min(1.0, body / (self.displacement_atr_mult * atr_val))
            direction = "bullish" if bullish else "bearish"
            obs.append(OrderBlock(
                direction=direction,
                high=highs[ob_idx],
                low=lows[ob_idx],
                bar_index=ob_idx,
                strength=strength,
            ))

        return obs

    def mark_mitigated(
        self, obs: List[OrderBlock], df: pd.DataFrame
    ) -> List[OrderBlock]:
        """Return new list with mitigated flag updated."""
        closes = df["close"].values
        result: List[OrderBlock] = []
        for ob in obs:
            mitigated = ob.mitigated
            for i in range(ob.bar_index + 1, len(closes)):
                if ob.direction == "bullish" and closes[i] < ob.low:
                    mitigated = True
                    break
                if ob.direction == "bearish" and closes[i] > ob.high:
                    mitigated = True
                    break
            result.append(OrderBlock(
                direction=ob.direction,
                high=ob.high,
                low=ob.low,
                bar_index=ob.bar_index,
                strength=ob.strength,
                mitigated=mitigated,
            ))
        return result


def _last_opposing(closes, opens, start: int, end: int, bearish: bool):
    """Last index in [start, end) where the candle opposes the given direction."""
    for j in range(end - 1, start - 1, -1):
        if bearish and closes[j] < opens[j]:
            return j
        if not bearish and closes[j] > opens[j]:
            return j
    return None
