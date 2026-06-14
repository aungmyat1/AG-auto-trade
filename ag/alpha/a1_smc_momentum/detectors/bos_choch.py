"""Break of Structure (BOS) and Change of Character (CHOCH) detector.

BOS:   price closes beyond a prior swing high/low in the direction of the current trend.
CHOCH: first BOS in the OPPOSITE direction — potential trend reversal signal.

Swing high/low definition: bar i is a swing high if highs[i] >= max of the
n bars before and after it (n = swing_lookback).  Mirror for lows.

# ⚠️  FRAGILE — SMC as a standalone signal has no edge on GC H1 (see
# research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md).
# This module is a CONTEXT FILTER only: it answers WHERE (structure breaks),
# never WHEN (entry timing).  Entry decisions live in AlphaModule.propose().
# NOTE: ChoCH/BOS is used as a WHEN trigger only for A0_MVP (expected FRAGILE).
# For A1, it is a WHERE context signal combined with ≥2-of-3 WHEN filters.
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from .base import StructureBreak, compute_atr


class BosChochDetector:
    def __init__(
        self,
        swing_lookback: int = 5,
        atr_window: int = 14,
    ) -> None:
        self.swing_lookback = swing_lookback
        self.atr_window = atr_window

    def detect(self, df: pd.DataFrame) -> List[StructureBreak]:
        n = self.swing_lookback
        min_bars = 2 * n + self.atr_window + 1
        if len(df) < min_bars:
            return []

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        atr = compute_atr(df, self.atr_window)

        sh_indices = _swing_highs(highs, n)
        sl_indices = _swing_lows(lows, n)

        breaks: List[StructureBreak] = []
        current_trend: Optional[str] = None
        last_sh_price: Optional[float] = None
        last_sl_price: Optional[float] = None

        for i in range(2 * n + 1, len(df)):
            # Only use swings confirmed before the look-back window of bar i
            relevant_sh = [h for h in sh_indices if h < i - n]
            relevant_sl = [sl for sl in sl_indices if sl < i - n]

            if relevant_sh:
                last_sh_price = highs[relevant_sh[-1]]
            if relevant_sl:
                last_sl_price = lows[relevant_sl[-1]]

            if last_sh_price is None or last_sl_price is None:
                continue

            atr_val = atr.iloc[i] or 1.0
            close = closes[i]

            if close > last_sh_price:
                btype = "CHOCH" if current_trend == "bearish" else "BOS"
                strength = min(1.0, (close - last_sh_price) / atr_val)
                breaks.append(StructureBreak(
                    type=btype,
                    direction="bullish",
                    price=last_sh_price,
                    bar_index=i,
                    strength=strength,
                ))
                current_trend = "bullish"

            elif close < last_sl_price:
                btype = "CHOCH" if current_trend == "bullish" else "BOS"
                strength = min(1.0, (last_sl_price - close) / atr_val)
                breaks.append(StructureBreak(
                    type=btype,
                    direction="bearish",
                    price=last_sl_price,
                    bar_index=i,
                    strength=strength,
                ))
                current_trend = "bearish"

        return breaks


def _swing_highs(highs: np.ndarray, n: int) -> List[int]:
    result = []
    for i in range(n, len(highs) - n):
        if highs[i] >= max(highs[i - n: i + n + 1]):
            result.append(i)
    return result


def _swing_lows(lows: np.ndarray, n: int) -> List[int]:
    result = []
    for i in range(n, len(lows) - n):
        if lows[i] <= min(lows[i - n: i + n + 1]):
            result.append(i)
    return result
