"""
Market Regime Classifier — instrument-agnostic.

Classifies each bar into one of four regimes:
  COMPRESSION  ATR%ile ≤ 20th, ADX ≥ 20   squeeze / breakout prep
  NORMAL       ATR%ile 20–60th, ADX ≥ 20   standard trend conditions
  EXPANSION    ATR%ile ≥ 60th, ADX ≥ 20    strong momentum
  CHOP         ADX < 20 (any ATR)           no directional conviction

Adapted from auto-trade-system/app/strategies/regime_detector.py.
No Bybit coupling; works on any OHLCV DataFrame.

Requirements:
  pip install pandas numpy ta  (or pandas-ta)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class Regime(str, Enum):
    COMPRESSION = "compression"
    NORMAL = "normal"
    EXPANSION = "expansion"
    CHOP = "chop"

    @property
    def size_multiplier(self) -> float:
        return {
            Regime.COMPRESSION: 0.50,
            Regime.NORMAL: 0.75,
            Regime.EXPANSION: 1.00,
            Regime.CHOP: 0.25,
        }[self]


@dataclass
class RegimeResult:
    regime: Regime
    atr_percentile: float    # 0–100
    adx: float
    ema50_slope_pct: float   # 5-bar EMA-50 slope as % of price
    htf_bull: Optional[bool] = None   # 4H/HTF EMA50 > EMA200; None = insufficient


class RegimeClassifier:
    """
    Classify a bar window into a market regime.

    Usage:
        clf = RegimeClassifier()
        result = clf.classify(df_ohlcv)  # df with open/high/low/close/volume cols
    """

    def __init__(
        self,
        atr_window: int = 14,
        atr_lookback: int = 100,
        adx_window: int = 14,
        ema_short: int = 50,
        ema_long: int = 200,
        adx_threshold: float = 20.0,
    ) -> None:
        self.atr_window = atr_window
        self.atr_lookback = atr_lookback
        self.adx_window = adx_window
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.adx_threshold = adx_threshold

    def classify(self, df: pd.DataFrame) -> RegimeResult:
        """
        Classify the current regime using the last bar of df.

        df must have columns: open, high, low, close, volume
        and at least max(200, atr_lookback + atr_window) bars.
        """
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        atr = self._atr(df)
        adx = self._adx(df)
        ema50 = df["close"].ewm(span=self.ema_short, adjust=False).mean()
        ema200 = df["close"].ewm(span=self.ema_long, adjust=False).mean()

        # ATR percentile in lookback window
        recent_atr = atr.iloc[-self.atr_lookback:]
        current_atr = float(atr.iloc[-1])
        atr_pct = float((recent_atr < current_atr).sum() / len(recent_atr) * 100)

        current_adx = float(adx.iloc[-1])
        current_price = float(df["close"].iloc[-1])

        # EMA slope: 5-bar % change of EMA50
        ema50_slope = 0.0
        if len(ema50) >= 6:
            ema50_slope = (float(ema50.iloc[-1]) - float(ema50.iloc[-6])) / float(ema50.iloc[-6]) * 100

        # HTF bias: EMA50 vs EMA200 at last bar
        htf_bull: Optional[bool] = None
        if len(ema50) >= self.ema_long:
            htf_bull = float(ema50.iloc[-1]) > float(ema200.iloc[-1])

        # Classify
        if current_adx < self.adx_threshold:
            regime = Regime.CHOP
        elif atr_pct <= 20:
            regime = Regime.COMPRESSION
        elif atr_pct >= 60:
            regime = Regime.EXPANSION
        else:
            regime = Regime.NORMAL

        return RegimeResult(
            regime=regime,
            atr_percentile=atr_pct,
            adx=current_adx,
            ema50_slope_pct=ema50_slope,
            htf_bull=htf_bull,
        )

    def _atr(self, df: pd.DataFrame) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"].shift(1)
        tr = pd.concat(
            [high - low, (high - close).abs(), (low - close).abs()], axis=1
        ).max(axis=1)
        return tr.ewm(span=self.atr_window, adjust=False).mean()

    def _adx(self, df: pd.DataFrame) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]
        w = self.adx_window

        up_move = high.diff()
        down_move = -low.diff()
        dm_plus = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        dm_minus = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr = pd.concat(
            [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1
        ).max(axis=1)

        atr_s = pd.Series(tr).ewm(span=w, adjust=False).mean()
        di_plus = 100 * pd.Series(dm_plus).ewm(span=w, adjust=False).mean() / (atr_s + 1e-10)
        di_minus = 100 * pd.Series(dm_minus).ewm(span=w, adjust=False).mean() / (atr_s + 1e-10)

        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus + 1e-10)
        return dx.ewm(span=w, adjust=False).mean()
