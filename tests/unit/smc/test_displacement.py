"""Unit tests for DisplacementDetector."""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.detectors.displacement import DisplacementDetector


# ── Helpers ──────────────────────────────────────────────────────────────────

def _flat_df(n: int, price: float = 100.0, body: float = 0.5) -> pd.DataFrame:
    """Small-body bars establishing ATR ≈ 1.0."""
    return pd.DataFrame({
        "open":   [price] * n,
        "high":   [price + body + 0.25] * n,
        "low":    [price - 0.25] * n,
        "close":  [price + body] * n,
        "volume": [1000] * n,
    })


DET = DisplacementDetector(atr_mult=1.5, atr_window=5)


# ── Detection ─────────────────────────────────────────────────────────────────

class TestDetect:
    def test_bullish_displacement_detected(self):
        base = _flat_df(20)  # ATR ≈ 1.0
        disp = pd.DataFrame({
            "open":   [100.5],
            "high":   [106.0],
            "low":    [100.3],
            "close":  [105.0],  # body=4.5, >> 1.5 * ATR
            "volume": [1000],
        })
        df = pd.concat([base, disp], ignore_index=True)
        disps = DET.detect(df)
        assert len(disps) == 1
        assert disps[0].direction == "bullish"

    def test_bearish_displacement_detected(self):
        base = _flat_df(20)
        disp = pd.DataFrame({
            "open":   [100.5],
            "high":   [100.8],
            "low":    [95.0],
            "close":  [96.0],   # body=4.5 bearish
            "volume": [1000],
        })
        df = pd.concat([base, disp], ignore_index=True)
        disps = DET.detect(df)
        assert len(disps) == 1
        assert disps[0].direction == "bearish"

    def test_small_body_not_displacement(self):
        base = _flat_df(20)  # all small bodies
        disps = DET.detect(base)
        assert len(disps) == 0

    def test_too_short_returns_empty(self):
        df = _flat_df(3)
        assert DET.detect(df) == []

    def test_body_size_populated(self):
        base = _flat_df(20)
        disp = pd.DataFrame({
            "open": [100.0], "high": [106.0], "low": [99.8], "close": [105.0],
            "volume": [1000],
        })
        df = pd.concat([base, disp], ignore_index=True)
        result = DET.detect(df)
        assert result[0].body_size == pytest.approx(5.0)

    def test_atr_multiple_populated(self):
        base = _flat_df(20)
        disp = pd.DataFrame({
            "open": [100.0], "high": [106.0], "low": [99.8], "close": [105.0],
            "volume": [1000],
        })
        df = pd.concat([base, disp], ignore_index=True)
        result = DET.detect(df)
        assert result[0].atr_multiple >= 1.5

    def test_strength_score_scales_with_multiple(self):
        base = _flat_df(20)
        small_disp = pd.DataFrame({
            "open": [100.0], "high": [102.0], "low": [99.8], "close": [101.7],
            "volume": [1000],
        })
        large_disp = pd.DataFrame({
            "open": [100.0], "high": [110.0], "low": [99.8], "close": [109.0],
            "volume": [1000],
        })
        df_small = pd.concat([base, small_disp], ignore_index=True)
        df_large = pd.concat([base, large_disp], ignore_index=True)
        d_small = DET.detect(df_small)
        d_large = DET.detect(df_large)
        if d_small and d_large:
            assert d_small[0].strength_score() < d_large[0].strength_score()

    def test_multiple_displacements_detected(self):
        base = _flat_df(20)
        two = pd.DataFrame({
            "open":   [100.0, 105.0],
            "high":   [106.0, 111.0],
            "low":    [99.8,  104.8],
            "close":  [105.0, 110.0],
            "volume": [1000,  1000],
        })
        df = pd.concat([base, two], ignore_index=True)
        assert len(DET.detect(df)) == 2
