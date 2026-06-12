"""Shared dataclasses and ATR helper for all SMC detectors."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class OrderBlock:
    direction: str  # "bullish" | "bearish"
    high: float
    low: float
    bar_index: int
    strength: float  # 0–1
    mitigated: bool = False

    def is_mitigated(self) -> bool:
        return self.mitigated

    def strength_score(self) -> float:
        return self.strength


@dataclass
class FairValueGap:
    direction: str  # "bullish" | "bearish"
    high: float  # top of gap
    low: float   # bottom of gap
    bar_index: int  # middle candle index
    size_atr: float
    mitigated: bool = False

    def is_mitigated(self) -> bool:
        return self.mitigated

    def strength_score(self) -> float:
        return min(1.0, self.size_atr / 2.0)


@dataclass
class LiquidityLevel:
    direction: str  # "high" | "low"
    price: float
    bar_index: int
    sweep_confirmed: bool = False

    def is_mitigated(self) -> bool:
        return self.sweep_confirmed

    def strength_score(self) -> float:
        return 1.0 if self.sweep_confirmed else 0.5


@dataclass
class StructureBreak:
    type: str       # "BOS" | "CHOCH"
    direction: str  # "bullish" | "bearish"
    price: float    # the broken level
    bar_index: int
    strength: float  # 0–1

    def is_mitigated(self) -> bool:
        return False  # structure breaks are events, not zones

    def strength_score(self) -> float:
        return self.strength


@dataclass
class Displacement:
    direction: str  # "bullish" | "bearish"
    bar_index: int
    body_size: float
    atr_multiple: float  # body / atr

    def strength_score(self) -> float:
        return min(1.0, self.atr_multiple / 4.0)


def compute_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """True-range ATR — no external dependency."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window, min_periods=1).mean()
