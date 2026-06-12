"""Unit tests for LiquidityDetector.

Uses swing_lookback=2, atr_window=5 to keep synthetic data short.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.detectors.liquidity import LiquidityDetector


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_df(opens, highs, lows, closes):
    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows, "close": closes,
        "volume": [1000] * len(opens),
    })


def _equal_highs_df(sweep: bool = False):
    """
    Two swing highs at nearly the same price (~115 ± 0.1).
    bars 0-2: base at 100
    bar 3-4:  approach; bar 3 has high 108
    bar 5:    swing high 1, high=115.0, then pullback
    bar 6-7:  pullback, highs 108, 107
    bar 8-9:  approach; bar 9 has high 108
    bar 10:   swing high 2, high=115.1 (within 0.3 ATR ≈ 0.3 of first)
    bar 11-12: pullback
    (optional) bar 13: sweep — wick above 115, close below (if sweep=True)
    """
    opens  = [100]*3 + [104, 108, 111,  109, 106, 104, 108, 111,  109, 106]
    highs  = [101]*3 + [108, 112, 115.0, 109, 108, 108, 112, 115.0, 109, 106]
    lows   = [99] *3 + [103, 107, 110,  107, 104, 103, 107, 110,  107, 104]
    closes = [100]*3 + [106, 110, 112,  108, 106, 106, 110, 112,  108, 105]

    df = _make_df(opens, highs, lows, closes)

    if sweep:
        # Wick above 115.1, close below 115
        sweep_bar = pd.DataFrame({
            "open": [112], "high": [116.0], "low": [111.0], "close": [114.5],
            "volume": [1000],
        })
        df = pd.concat([df, sweep_bar], ignore_index=True)

    return df


def _equal_lows_df(sweep: bool = False):
    """
    Two swing lows at nearly the same price (~85 ± 0.1).
    """
    opens  = [100]*3 + [96, 92, 89,  91, 94, 96, 92, 89,  91, 94]
    highs  = [101]*3 + [97, 94, 91,  93, 96, 97, 94, 91,  93, 96]
    lows   = [99] *3 + [94, 88, 85.0, 88, 91, 94, 88, 85.1, 88, 91]
    closes = [100]*3 + [95, 90, 88,  90, 93, 95, 90, 88,  90, 93]

    df = _make_df(opens, highs, lows, closes)

    if sweep:
        # Wick below 85, close above 85.1
        sweep_bar = pd.DataFrame({
            "open": [88], "high": [89.0], "low": [84.0], "close": [86.0],
            "volume": [1000],
        })
        df = pd.concat([df, sweep_bar], ignore_index=True)

    return df


DET = LiquidityDetector(swing_lookback=2, cluster_atr_mult=0.5, atr_window=5)


# ── Detection ─────────────────────────────────────────────────────────────────

class TestDetect:
    def test_equal_highs_detected(self):
        df = _equal_highs_df()
        levels = DET.detect(df)
        highs = [lvl for lvl in levels if lvl.direction == "high"]
        assert len(highs) >= 1

    def test_equal_highs_price(self):
        df = _equal_highs_df()
        highs = [lvl for lvl in DET.detect(df) if lvl.direction == "high"]
        prices = [h.price for h in highs]
        assert any(abs(p - 115.0) < 0.5 for p in prices)

    def test_equal_lows_detected(self):
        df = _equal_lows_df()
        levels = DET.detect(df)
        lows = [lvl for lvl in levels if lvl.direction == "low"]
        assert len(lows) >= 1

    def test_too_short_returns_empty(self):
        df = pd.DataFrame({
            "open": [100]*5, "high": [101]*5, "low": [99]*5,
            "close": [100]*5, "volume": [1000]*5,
        })
        assert DET.detect(df) == []

    def test_unswept_by_default(self):
        levels = DET.detect(_equal_highs_df(sweep=False))
        assert all(not lvl.sweep_confirmed for lvl in levels)


# ── Sweep confirmation ────────────────────────────────────────────────────────

class TestSweep:
    def test_sweep_high_confirmed(self):
        df = _equal_highs_df(sweep=True)
        levels = DET.detect(df)
        highs = [lvl for lvl in levels if lvl.direction == "high"]
        assert any(lvl.sweep_confirmed for lvl in highs)

    def test_sweep_low_confirmed(self):
        df = _equal_lows_df(sweep=True)
        levels = DET.detect(df)
        lows = [lvl for lvl in levels if lvl.direction == "low"]
        assert any(lvl.sweep_confirmed for lvl in lows)

    def test_strength_score_higher_when_swept(self):
        swept = next(lvl for lvl in DET.detect(_equal_highs_df(sweep=True)) if lvl.direction == "high")
        assert swept.strength_score() == pytest.approx(1.0)

    def test_strength_score_lower_when_not_swept(self):
        unswept = next(lvl for lvl in DET.detect(_equal_highs_df(sweep=False)) if lvl.direction == "high")
        assert unswept.strength_score() == pytest.approx(0.5)
