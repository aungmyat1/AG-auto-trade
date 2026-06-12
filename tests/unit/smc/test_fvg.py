"""Unit tests for FairValueGapDetector."""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.detectors.fvg import FairValueGapDetector


# ── Helpers ──────────────────────────────────────────────────────────────────

def _flat_df(n: int, price: float = 100.0) -> pd.DataFrame:
    """n bars with ATR ≈ 1.0 (body=0.5, wicks=0.25 each)."""
    return pd.DataFrame({
        "open":   [price] * n,
        "high":   [price + 0.75] * n,
        "low":    [price - 0.25] * n,
        "close":  [price + 0.5] * n,
        "volume": [1000] * n,
    })


def _bullish_fvg_df(gap: float = 2.0):
    """
    15 flat bars (ATR ≈ 1.0) then 3 candles creating a bullish FVG:
      c1: high=101
      c2: middle (can be anything)
      c3: low=101+gap  →  c3.low - c1.high = gap (bullish FVG)
    """
    base = _flat_df(15)
    c1_high = 101.0
    c3_low = c1_high + gap
    extra = pd.DataFrame({
        "open":   [100.0,  100.0,    c3_low + 1.0],
        "high":   [c1_high, 102.0,   c3_low + 2.0],
        "low":    [99.5,   99.8,     c3_low],
        "close":  [100.5,  101.5,    c3_low + 1.5],
        "volume": [1000,   1000,     1000],
    })
    return pd.concat([base, extra], ignore_index=True)


def _bearish_fvg_df(gap: float = 2.0):
    """
    15 flat bars then 3 candles creating a bearish FVG:
      c1: low=99
      c2: middle
      c3: high=99-gap  →  c1.low - c3.high = gap (bearish FVG)
    """
    base = _flat_df(15)
    c1_low = 99.0
    c3_high = c1_low - gap
    extra = pd.DataFrame({
        "open":   [100.0,  99.5,    c3_high - 0.5],
        "high":   [100.5,  100.0,   c3_high],
        "low":    [c1_low, 98.5,    c3_high - 1.5],
        "close":  [99.5,   98.8,    c3_high - 1.0],
        "volume": [1000,   1000,    1000],
    })
    return pd.concat([base, extra], ignore_index=True)


DET = FairValueGapDetector(min_size_atr=0.5, atr_window=5)


# ── Detection ─────────────────────────────────────────────────────────────────

class TestDetect:
    def test_bullish_fvg_detected(self):
        df = _bullish_fvg_df(gap=2.0)
        fvgs = DET.detect(df)
        bullish = [f for f in fvgs if f.direction == "bullish"]
        assert len(bullish) >= 1

    def test_bullish_fvg_price_bounds(self):
        df = _bullish_fvg_df(gap=2.0)
        fvg = next(f for f in DET.detect(df) if f.direction == "bullish")
        # gap high = c3.low, gap low = c1.high
        assert fvg.low == pytest.approx(101.0)   # c1.high
        assert fvg.high == pytest.approx(103.0)  # c3.low = 101 + 2

    def test_bearish_fvg_detected(self):
        df = _bearish_fvg_df(gap=2.0)
        fvgs = DET.detect(df)
        bearish = [f for f in fvgs if f.direction == "bearish"]
        assert len(bearish) >= 1

    def test_bearish_fvg_price_bounds(self):
        df = _bearish_fvg_df(gap=2.0)
        fvg = next(f for f in DET.detect(df) if f.direction == "bearish")
        # gap high = c1.low, gap low = c3.high
        assert fvg.high == pytest.approx(99.0)  # c1.low
        assert fvg.low == pytest.approx(97.0)   # c3.high = 99 - 2

    def test_no_fvg_when_candles_overlap(self):
        """No gap when c3.low <= c1.high."""
        base = _flat_df(15)
        extra = pd.DataFrame({
            "open":   [100.0, 100.0, 100.0],
            "high":   [101.0, 102.0, 101.5],
            "low":    [99.5,  99.8,  100.5],  # c3.low=100.5 <= c1.high=101 → no gap
            "close":  [100.5, 101.5, 101.0],
            "volume": [1000,  1000,  1000],
        })
        df = pd.concat([base, extra], ignore_index=True)
        bullish = [f for f in DET.detect(df) if f.direction == "bullish"]
        # The gap here is 100.5 - 101 = -0.5 (negative → no FVG)
        assert len(bullish) == 0

    def test_too_short_returns_empty(self):
        df = _flat_df(5)
        assert DET.detect(df) == []

    def test_size_atr_populated(self):
        fvgs = DET.detect(_bullish_fvg_df(gap=2.0))
        for f in fvgs:
            assert f.size_atr > 0

    def test_fvg_bar_index_is_middle_candle(self):
        """FVG bar_index should point to the middle (second) candle of the 3-bar pattern."""
        df = _bullish_fvg_df(gap=2.0)
        fvg = next(f for f in DET.detect(df) if f.direction == "bullish")
        # Middle candle of the 3-bar FVG group = index 16 (base=15, c1=15, c2=16, c3=17)
        assert fvg.bar_index == 16


# ── Mitigation ────────────────────────────────────────────────────────────────

class TestMarkMitigated:
    def test_bullish_fvg_mitigated_when_close_fills_gap(self):
        base = _bullish_fvg_df(gap=2.0)
        fvg = next(f for f in DET.detect(base) if f.direction == "bullish")
        # fvg.low = 101.0; fill it by closing at or below 101.0
        fill_bar = pd.DataFrame({
            "open": [103.0], "high": [103.5], "low": [100.5], "close": [100.9],
            "volume": [1000],
        })
        df = pd.concat([base, fill_bar], ignore_index=True)
        result = DET.mark_mitigated([fvg], df)
        assert result[0].mitigated is True

    def test_bullish_fvg_not_mitigated_while_price_above(self):
        base = _bullish_fvg_df(gap=2.0)
        fvg = next(f for f in DET.detect(base) if f.direction == "bullish")
        extra = pd.DataFrame({
            "open": [104.0, 105.0], "high": [105.0, 106.0],
            "low": [103.5, 104.5], "close": [104.5, 105.5],
            "volume": [1000, 1000],
        })
        df = pd.concat([base, extra], ignore_index=True)
        result = DET.mark_mitigated([fvg], df)
        assert result[0].mitigated is False
