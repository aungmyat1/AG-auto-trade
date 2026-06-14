"""Liquidity level detector.

Equal highs/lows within cluster_atr_mult * ATR of each other form a liquidity pool.
A sweep is confirmed when price wicks beyond the level then closes back inside.

# ⚠️  FRAGILE — SMC as a standalone signal has no edge on GC H1 (see
# research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md).
# This module is a CONTEXT FILTER only: it answers WHERE (liquidity zones),
# never WHEN (entry timing).  Entry decisions live in AlphaModule.propose().
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from .base import LiquidityLevel, compute_atr


class LiquidityDetector:
    def __init__(
        self,
        swing_lookback: int = 5,
        cluster_atr_mult: float = 0.3,
        atr_window: int = 14,
    ) -> None:
        self.swing_lookback = swing_lookback
        self.cluster_atr_mult = cluster_atr_mult
        self.atr_window = atr_window

    def detect(self, df: pd.DataFrame) -> List[LiquidityLevel]:
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

        levels: List[LiquidityLevel] = []
        seen_high: set = set()
        seen_low: set = set()

        # Equal highs → sell-side liquidity above price
        for idx in sh_indices:
            if idx in seen_high:
                continue
            atr_val = atr.iloc[idx] or 1.0
            cluster = [
                j for j in sh_indices
                if j != idx and abs(highs[j] - highs[idx]) < self.cluster_atr_mult * atr_val
            ]
            if not cluster:
                continue
            seen_high.add(idx)
            seen_high.update(cluster)
            liq = LiquidityLevel(direction="high", price=highs[idx], bar_index=idx)
            liq = _check_sweep_high(liq, highs, closes, len(df))
            levels.append(liq)

        # Equal lows → buy-side liquidity below price
        for idx in sl_indices:
            if idx in seen_low:
                continue
            atr_val = atr.iloc[idx] or 1.0
            cluster = [
                j for j in sl_indices
                if j != idx and abs(lows[j] - lows[idx]) < self.cluster_atr_mult * atr_val
            ]
            if not cluster:
                continue
            seen_low.add(idx)
            seen_low.update(cluster)
            liq = LiquidityLevel(direction="low", price=lows[idx], bar_index=idx)
            liq = _check_sweep_low(liq, lows, closes, len(df))
            levels.append(liq)

        return levels


def _check_sweep_high(
    liq: LiquidityLevel, highs: np.ndarray, closes: np.ndarray, n_bars: int
) -> LiquidityLevel:
    """Sweep: wick above the level, close below it."""
    for k in range(liq.bar_index + 1, n_bars):
        if highs[k] > liq.price and closes[k] < liq.price:
            return LiquidityLevel(
                direction=liq.direction,
                price=liq.price,
                bar_index=liq.bar_index,
                sweep_confirmed=True,
            )
    return liq


def _check_sweep_low(
    liq: LiquidityLevel, lows: np.ndarray, closes: np.ndarray, n_bars: int
) -> LiquidityLevel:
    """Sweep: wick below the level, close above it."""
    for k in range(liq.bar_index + 1, n_bars):
        if lows[k] < liq.price and closes[k] > liq.price:
            return LiquidityLevel(
                direction=liq.direction,
                price=liq.price,
                bar_index=liq.bar_index,
                sweep_confirmed=True,
            )
    return liq


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
