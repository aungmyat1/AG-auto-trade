"""Unit tests for BosChochDetector.

Uses swing_lookback=2, atr_window=5 to keep synthetic data short (~25 bars).
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.detectors.bos_choch import BosChochDetector


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_df(opens, highs, lows, closes):
    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows, "close": closes,
        "volume": [1000] * len(opens),
    })


def _bos_bullish_df():
    """
    Swing high at bar 5 (high=115): bars 3-4 have lower highs, bars 6-7 have lower highs.
    At bar 9: close=116 > 115 → BOS bullish (bar 5 is relevant because 5 < 9-2=7).

    Layout (n=2):
      bars 0-2: base, high≈101
      bar  3-4: approach, high≈108
      bar  5:   swing high, high=115, close=112
      bar  6-7: pullback, high≈108, close≈106
      bar  8:   re-approach, close=113 (not yet above 115)
      bar  9:   breakout, close=116 > 115  → BOS bullish
    """
    opens  = [100, 100, 100,  106,  109,  110,  108,  107,  108,  110]
    highs  = [101, 101, 101,  108,  112,  115,  109,  108,  113,  117]
    lows   = [99,  99,  99,  105,  107,  110,  105,  104,  106,  109]
    closes = [100, 100, 100,  107,  110,  112,  106,  105,  113,  116]
    return _make_df(opens, highs, lows, closes)


def _choch_after_bullish_bos():
    """
    Establish a bullish BOS first (same as above, bars 0-9),
    then create a bearish CHOCH by closing below swing low.

    Swing low at bar 12 (low=88): bars 10-11 have higher lows, bars 13-14 have higher lows.
    At bar 15+: close < 88 → CHOCH bearish (since current trend = bullish after bar 9).
    """
    # first part: BOS bullish (10 bars)
    opens1  = [100, 100, 100, 106, 109, 110, 108, 107, 108, 110]
    highs1  = [101, 101, 101, 108, 112, 115, 109, 108, 113, 117]
    lows1   = [99,  99,  99,  105, 107, 110, 105, 104, 106, 109]
    closes1 = [100, 100, 100, 107, 110, 112, 106, 105, 113, 116]

    # second part: fall, swing low, then CHOCH
    # bar 10-11: high lows (lows 95, 94)
    # bar 12: swing low (low=88, close=90)
    # bar 13-14: higher lows again (lows 93, 95)
    # bar 15: close=87 < 88 → CHOCH bearish
    opens2  = [115, 113,  100,  92, 94,  90]
    highs2  = [116, 114,  101,  95, 96,  92]
    lows2   = [95,  94,    88,  93, 95,  85]
    closes2 = [113, 111,   90,  94, 95,  87]

    opens  = opens1  + opens2
    highs  = highs1  + highs2
    lows   = lows1   + lows2
    closes = closes1 + closes2
    return _make_df(opens, highs, lows, closes)


DET = BosChochDetector(swing_lookback=2, atr_window=5)


# ── BOS tests ─────────────────────────────────────────────────────────────────

class TestBos:
    def test_bullish_bos_detected(self):
        df = _bos_bullish_df()
        breaks = DET.detect(df)
        bos = [b for b in breaks if b.type == "BOS" and b.direction == "bullish"]
        assert len(bos) >= 1

    def test_bos_price_is_broken_level(self):
        df = _bos_bullish_df()
        bos = next(b for b in DET.detect(df) if b.type == "BOS" and b.direction == "bullish")
        # The broken level is the swing high at bar 5 = 115
        assert bos.price == pytest.approx(115.0)

    def test_bos_bar_index_after_swing(self):
        df = _bos_bullish_df()
        bos = next(b for b in DET.detect(df) if b.type == "BOS" and b.direction == "bullish")
        # Break happens at bar 9
        assert bos.bar_index == 9

    def test_too_short_returns_empty(self):
        df = pd.DataFrame({
            "open": [100]*5, "high": [101]*5, "low": [99]*5,
            "close": [100]*5, "volume": [1000]*5,
        })
        assert DET.detect(df) == []

    def test_strength_between_0_and_1(self):
        breaks = DET.detect(_bos_bullish_df())
        for b in breaks:
            assert 0.0 < b.strength <= 1.0


# ── CHOCH tests ───────────────────────────────────────────────────────────────

class TestChoch:
    def test_bearish_choch_after_bullish_trend(self):
        df = _choch_after_bullish_bos()
        breaks = DET.detect(df)
        choch = [b for b in breaks if b.type == "CHOCH" and b.direction == "bearish"]
        assert len(choch) >= 1

    def test_choch_comes_after_bos(self):
        df = _choch_after_bullish_bos()
        breaks = DET.detect(df)
        bos_indices = [b.bar_index for b in breaks if b.type == "BOS"]
        choch_indices = [b.bar_index for b in breaks if b.type == "CHOCH"]
        assert bos_indices  # at least one BOS
        assert choch_indices  # at least one CHOCH
        assert min(choch_indices) > min(bos_indices)

    def test_is_mitigated_always_false(self):
        breaks = DET.detect(_bos_bullish_df())
        for b in breaks:
            assert b.is_mitigated() is False
