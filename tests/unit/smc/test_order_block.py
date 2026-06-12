"""Unit tests for OrderBlockDetector.

All tests use displacement_atr_mult=0.5, atr_window=5, lookback=3 to keep
synthetic DataFrames short (~20 bars) while exercising the same code paths
as the production defaults.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.detectors.order_block import OrderBlockDetector


# ── Helpers ──────────────────────────────────────────────────────────────────

def _flat_df(n: int = 15, price: float = 100.0, body: float = 0.5) -> pd.DataFrame:
    """n identical candles; ATR ≈ body + 0.5 (wick each side)."""
    h = price + body + 0.25
    lo = price - 0.25
    return pd.DataFrame({
        "open":   [price] * n,
        "high":   [h] * n,
        "low":    [lo] * n,
        "close":  [price + body] * n,  # bullish body
        "volume": [1000] * n,
    })


def _bullish_ob_df():
    """
    15 flat bars + 1 bearish OB candle + 1 large bullish displacement.

    Flat bar ATR ≈ 1.0 (body=0.5, wick=0.5 total).
    OB (bar 15): o=101 h=101.5 l=99.5 c=100  (bearish, c<o)
    Displacement (bar 16): o=100 h=108 l=99.8 c=107
      body=7 >> 0.5 * ATR ≈ 0.5 * 1.0 = 0.5
      close=107 > max(highs[13:16]) ≈ 100.75  ✓ breaks previous high
    """
    base = _flat_df(15)
    extra = pd.DataFrame({
        "open":   [101.0,  100.0],
        "high":   [101.5,  108.0],
        "low":    [99.5,    99.8],
        "close":  [100.0,  107.0],
        "volume": [1000,   1000],
    })
    return pd.concat([base, extra], ignore_index=True)


def _bearish_ob_df():
    """
    15 flat bars + 1 bullish OB candle + 1 large bearish displacement.

    OB (bar 15): o=99 h=100.5 l=98.5 c=100 (bullish, c>o)
    Displacement (bar 16): o=100 h=100.2 l=92 c=93  (body=7, bearish)
      close=93 < min(lows[13:16]) ≈ 99.75  ✓ breaks previous low
    """
    base = _flat_df(15)
    extra = pd.DataFrame({
        "open":   [99.0,   100.0],
        "high":   [100.5,  100.2],
        "low":    [98.5,    92.0],
        "close":  [100.0,   93.0],
        "volume": [1000,   1000],
    })
    return pd.concat([base, extra], ignore_index=True)


DET = OrderBlockDetector(displacement_atr_mult=0.5, atr_window=5, lookback=3)


# ── Detection ─────────────────────────────────────────────────────────────────

class TestDetect:
    def test_bullish_ob_detected(self):
        df = _bullish_ob_df()
        obs = DET.detect(df)
        assert len(obs) == 1
        assert obs[0].direction == "bullish"

    def test_bullish_ob_price_bounds(self):
        df = _bullish_ob_df()
        ob = DET.detect(df)[0]
        assert ob.high == pytest.approx(101.5)
        assert ob.low == pytest.approx(99.5)

    def test_bullish_ob_bar_index(self):
        df = _bullish_ob_df()
        ob = DET.detect(df)[0]
        assert ob.bar_index == 15  # the OB is at the bearish candle

    def test_bearish_ob_detected(self):
        df = _bearish_ob_df()
        obs = DET.detect(df)
        assert len(obs) == 1
        assert obs[0].direction == "bearish"

    def test_bearish_ob_price_bounds(self):
        df = _bearish_ob_df()
        ob = DET.detect(df)[0]
        assert ob.high == pytest.approx(100.5)
        assert ob.low == pytest.approx(98.5)

    def test_no_ob_without_structure_break(self):
        """Displacement with close below prior high → no OB."""
        base = _flat_df(15)
        # body=0.6, close=100.6 does NOT exceed prior high ≈ 100.75
        no_break = pd.DataFrame({
            "open":   [100.0],
            "high":   [100.8],
            "low":    [99.8],
            "close":  [100.6],
            "volume": [1000],
        })
        df = pd.concat([base, no_break], ignore_index=True)
        obs = DET.detect(df)
        assert len(obs) == 0

    def test_too_short_returns_empty(self):
        df = _flat_df(5)
        obs = DET.detect(df)
        assert obs == []

    def test_strength_between_0_and_1(self):
        obs = DET.detect(_bullish_ob_df())
        assert 0.0 < obs[0].strength <= 1.0

    def test_unmitigated_by_default(self):
        obs = DET.detect(_bullish_ob_df())
        assert obs[0].mitigated is False


# ── Mitigation ────────────────────────────────────────────────────────────────

class TestMarkMitigated:
    def test_bullish_ob_mitigated_when_close_below_low(self):
        base = _bullish_ob_df()
        ob = DET.detect(base)[0]  # low = 99.5
        extra = pd.DataFrame({
            "open":   [107.0],
            "high":   [108.0],
            "low":    [99.0],
            "close":  [99.2],   # 99.2 < ob.low=99.5 → mitigated
            "volume": [1000],
        })
        df = pd.concat([base, extra], ignore_index=True)
        result = DET.mark_mitigated([ob], df)
        assert result[0].mitigated is True

    def test_bullish_ob_not_mitigated_while_above_low(self):
        base = _bullish_ob_df()
        ob = DET.detect(base)[0]  # low = 99.5
        extra = pd.DataFrame({
            "open":   [107.0, 106.5],
            "high":   [108.0, 107.0],
            "low":    [106.0, 105.5],
            "close":  [106.5, 106.0],  # both well above 99.5
            "volume": [1000, 1000],
        })
        df = pd.concat([base, extra], ignore_index=True)
        result = DET.mark_mitigated([ob], df)
        assert result[0].mitigated is False

    def test_bearish_ob_mitigated_when_close_above_high(self):
        base = _bearish_ob_df()
        ob = DET.detect(base)[0]  # high = 100.5
        extra = pd.DataFrame({
            "open":   [93.0],
            "high":   [101.0],
            "low":    [92.5],
            "close":  [100.8],  # 100.8 > ob.high=100.5 → mitigated
            "volume": [1000],
        })
        df = pd.concat([base, extra], ignore_index=True)
        result = DET.mark_mitigated([ob], df)
        assert result[0].mitigated is True
