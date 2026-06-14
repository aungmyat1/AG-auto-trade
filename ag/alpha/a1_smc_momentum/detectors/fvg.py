"""Fair Value Gap (FVG / Imbalance) detector.

3-candle pattern:
  Bullish FVG: candle[i].low  > candle[i-2].high  (gap above candle i-2)
  Bearish FVG: candle[i].high < candle[i-2].low   (gap below candle i-2)

Gap must be >= min_size_atr * ATR(14) to avoid noise.

# ⚠️  FRAGILE — SMC as a standalone signal has no edge on GC H1 (see
# research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md).
# This module is a CONTEXT FILTER only: it answers WHERE (imbalance zones),
# never WHEN (entry timing).  Entry decisions live in AlphaModule.propose().
"""
from __future__ import annotations

from typing import List

import pandas as pd

from .base import FairValueGap, compute_atr


class FairValueGapDetector:
    def __init__(
        self,
        min_size_atr: float = 0.5,
        atr_window: int = 14,
    ) -> None:
        self.min_size_atr = min_size_atr
        self.atr_window = atr_window

    def detect(self, df: pd.DataFrame) -> List[FairValueGap]:
        if len(df) < self.atr_window + 3:
            return []

        atr = compute_atr(df, self.atr_window)
        highs = df["high"].values
        lows = df["low"].values

        fvgs: List[FairValueGap] = []
        for i in range(2, len(df)):
            atr_val = atr.iloc[i]
            if atr_val <= 0:
                continue

            # Bullish FVG
            gap = lows[i] - highs[i - 2]
            if gap > 0 and gap / atr_val >= self.min_size_atr:
                fvgs.append(FairValueGap(
                    direction="bullish",
                    high=lows[i],
                    low=highs[i - 2],
                    bar_index=i - 1,
                    size_atr=gap / atr_val,
                ))

            # Bearish FVG
            gap = lows[i - 2] - highs[i]
            if gap > 0 and gap / atr_val >= self.min_size_atr:
                fvgs.append(FairValueGap(
                    direction="bearish",
                    high=lows[i - 2],
                    low=highs[i],
                    bar_index=i - 1,
                    size_atr=gap / atr_val,
                ))

        return fvgs

    def mark_mitigated(
        self, fvgs: List[FairValueGap], df: pd.DataFrame
    ) -> List[FairValueGap]:
        """FVG is filled when price closes inside or through the gap."""
        closes = df["close"].values
        result: List[FairValueGap] = []
        for fvg in fvgs:
            mitigated = fvg.mitigated
            for i in range(fvg.bar_index + 1, len(closes)):
                if fvg.direction == "bullish" and closes[i] <= fvg.low:
                    mitigated = True
                    break
                if fvg.direction == "bearish" and closes[i] >= fvg.high:
                    mitigated = True
                    break
            result.append(FairValueGap(
                direction=fvg.direction,
                high=fvg.high,
                low=fvg.low,
                bar_index=fvg.bar_index,
                size_atr=fvg.size_atr,
                mitigated=mitigated,
            ))
        return result
