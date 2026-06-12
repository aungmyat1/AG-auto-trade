"""Displacement detector.

A displacement candle has a body >= atr_mult * ATR(atr_window),
signalling institutional momentum.  Default: body >= 1.8 * ATR(20).
"""
from __future__ import annotations

from typing import List

import pandas as pd

from .base import Displacement, compute_atr


class DisplacementDetector:
    def __init__(
        self,
        atr_mult: float = 1.8,
        atr_window: int = 20,
    ) -> None:
        self.atr_mult = atr_mult
        self.atr_window = atr_window

    def detect(self, df: pd.DataFrame) -> List[Displacement]:
        if len(df) < self.atr_window + 1:
            return []

        atr = compute_atr(df, self.atr_window)
        opens = df["open"].values
        closes = df["close"].values

        displacements: List[Displacement] = []
        for i in range(1, len(df)):
            body = abs(closes[i] - opens[i])
            atr_val = atr.iloc[i]
            if atr_val <= 0:
                continue
            mult = body / atr_val
            if mult >= self.atr_mult:
                direction = "bullish" if closes[i] > opens[i] else "bearish"
                displacements.append(Displacement(
                    direction=direction,
                    bar_index=i,
                    body_size=body,
                    atr_multiple=mult,
                ))

        return displacements
