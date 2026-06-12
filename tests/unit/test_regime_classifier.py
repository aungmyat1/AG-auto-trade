"""
Unit tests for RegimeClassifier.

Regime classification rules (from classifier.py):
  ADX < adx_threshold (20)                    → CHOP     (size_multiplier 0.25)
  ADX ≥ 20, ATR%ile ≤ 20                      → COMPRESSION (0.50)
  ADX ≥ 20, ATR%ile 20–60                     → NORMAL   (0.75)
  ADX ≥ 20, ATR%ile ≥ 60                      → EXPANSION (1.00)

Synthetic OHLCV construction notes:
- Needs ≥ max(ema_long, atr_lookback + atr_window) bars; default → 200.
- Using (atr_lookback=50, ema_long=100, adx_window=14, atr_window=14)
  for most tests to reduce required bars to 100.
- Columns case-insensitive (classifier normalises to lowercase).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ag.regime.classifier import Regime, RegimeClassifier, RegimeResult


# ── OHLCV factories ────────────────────────────────────────────────────────────

def _flat_ohlcv(n: int = 150, price: float = 2000.0) -> pd.DataFrame:
    """Perfectly flat price with near-zero range → ADX→0 → CHOP."""
    closes = np.full(n, price)
    return pd.DataFrame({
        "open":   closes,
        "high":   closes + 0.01,
        "low":    closes - 0.01,
        "close":  closes,
        "volume": np.full(n, 1000.0),
    })


def _trending_ohlcv(
    n: int = 200,
    start: float = 1000.0,
    step: float = 10.0,
    bar_size: float = 30.0,
    end_spike_bars: int = 20,
    end_spike_mult: float = 5.0,
) -> pd.DataFrame:
    """
    Consistent strong uptrend (→ ADX > 20) with large bars.

    The last `end_spike_bars` bars have `end_spike_mult` × normal bar size
    to push ATR%ile above 60 (EXPANSION).
    """
    closes = np.array([start + step * i for i in range(n)])
    highs = closes + bar_size
    lows = closes - bar_size
    # spike the last end_spike_bars
    highs[-end_spike_bars:] = closes[-end_spike_bars:] + bar_size * end_spike_mult
    lows[-end_spike_bars:] = closes[-end_spike_bars:] - bar_size * end_spike_mult
    return pd.DataFrame({
        "open":   closes - bar_size / 2,
        "high":   highs,
        "low":    lows,
        "close":  closes,
        "volume": np.full(n, 1000.0),
    })


def _compression_ohlcv(
    n: int = 200,
    start: float = 1000.0,
    step: float = 5.0,
    bar_size: float = 1.0,
    early_spike_bars: int = 100,
    early_spike_mult: float = 20.0,
) -> pd.DataFrame:
    """
    Consistent small uptrend (→ ADX > 20) with tiny recent bars.
    Early bars are large (high ATR in history), last bars are tiny
    (current ATR%ile < 20th pctile of lookback) → COMPRESSION.
    """
    closes = np.array([start + step * i for i in range(n)])
    highs = closes + bar_size
    lows  = closes - bar_size
    # spike early bars to inflate historical ATR
    highs[:early_spike_bars] = closes[:early_spike_bars] + bar_size * early_spike_mult
    lows[:early_spike_bars]  = closes[:early_spike_bars] - bar_size * early_spike_mult
    return pd.DataFrame({
        "open":   closes - bar_size / 2,
        "high":   highs,
        "low":    lows,
        "close":  closes,
        "volume": np.full(n, 1000.0),
    })


def _small_clf() -> RegimeClassifier:
    """Classifier with reduced window sizes so 150–200 bars suffice."""
    return RegimeClassifier(
        atr_window=14,
        atr_lookback=50,
        adx_window=14,
        ema_short=50,
        ema_long=100,
        adx_threshold=20.0,
    )


# ── Regime enum ───────────────────────────────────────────────────────────────

class TestRegimeEnum:
    def test_size_multiplier_chop(self):
        assert Regime.CHOP.size_multiplier == pytest.approx(0.25)

    def test_size_multiplier_compression(self):
        assert Regime.COMPRESSION.size_multiplier == pytest.approx(0.50)

    def test_size_multiplier_normal(self):
        assert Regime.NORMAL.size_multiplier == pytest.approx(0.75)

    def test_size_multiplier_expansion(self):
        assert Regime.EXPANSION.size_multiplier == pytest.approx(1.00)

    def test_all_regimes_have_multiplier(self):
        for r in Regime:
            assert 0 < r.size_multiplier <= 1.0


# ── RegimeClassifier.classify() ───────────────────────────────────────────────

class TestRegimeClassify:
    def test_chop_on_flat_price(self):
        clf = _small_clf()
        df = _flat_ohlcv(n=150)
        result = clf.classify(df)
        assert result.regime == Regime.CHOP
        assert result.adx < 20.0

    def test_expansion_on_strong_trend(self):
        clf = _small_clf()
        df = _trending_ohlcv(n=200, step=10.0, bar_size=30.0,
                             end_spike_bars=20, end_spike_mult=5.0)
        result = clf.classify(df)
        assert result.regime == Regime.EXPANSION
        assert result.adx >= 20.0
        assert result.atr_percentile >= 60.0

    def test_compression_on_small_bars_after_spike_history(self):
        clf = _small_clf()
        df = _compression_ohlcv(n=200, step=5.0, bar_size=1.0,
                                early_spike_bars=100, early_spike_mult=20.0)
        result = clf.classify(df)
        assert result.regime == Regime.COMPRESSION
        assert result.adx >= 20.0
        assert result.atr_percentile <= 20.0

    def test_result_type(self):
        clf = _small_clf()
        result = clf.classify(_flat_ohlcv(n=150))
        assert isinstance(result, RegimeResult)

    def test_result_fields_populated(self):
        clf = _small_clf()
        result = clf.classify(_trending_ohlcv(n=200))
        assert 0.0 <= result.atr_percentile <= 100.0
        assert result.adx >= 0.0
        assert isinstance(result.ema50_slope_pct, float)
        assert isinstance(result.regime, Regime)

    def test_htf_bull_none_when_insufficient_bars(self):
        clf = RegimeClassifier(ema_long=200)  # default ema_long
        # Only 150 bars — insufficient for EMA200
        result = clf.classify(_flat_ohlcv(n=150))
        assert result.htf_bull is None

    def test_htf_bull_populated_when_sufficient_bars(self):
        clf = _small_clf()  # ema_long=100
        df = _trending_ohlcv(n=200)
        result = clf.classify(df)
        assert result.htf_bull is not None  # 200 bars ≥ ema_long=100
        assert result.htf_bull is True  # uptrend → EMA50 > EMA200

    def test_column_names_case_insensitive(self):
        clf = _small_clf()
        df = _flat_ohlcv(n=150)
        df.columns = [c.upper() for c in df.columns]  # UPPERCASE cols
        result = clf.classify(df)
        assert result.regime == Regime.CHOP  # should normalise and work

    def test_size_multiplier_via_result(self):
        clf = _small_clf()
        chop_result = clf.classify(_flat_ohlcv(n=150))
        assert chop_result.regime.size_multiplier == pytest.approx(0.25)


# ── custom adx_threshold ──────────────────────────────────────────────────────

class TestCustomThreshold:
    def test_low_threshold_promotes_flat_to_non_chop(self):
        # With adx_threshold=0.0, even a nearly flat series may not be CHOP
        clf = RegimeClassifier(
            atr_window=14, atr_lookback=50, adx_window=14,
            ema_short=50, ema_long=100, adx_threshold=0.0,
        )
        df = _flat_ohlcv(n=150)
        result = clf.classify(df)
        # ADX ≥ 0 is always true → not CHOP regardless of market
        assert result.regime != Regime.CHOP

    def test_high_threshold_forces_chop(self):
        clf = RegimeClassifier(
            atr_window=14, atr_lookback=50, adx_window=14,
            ema_short=50, ema_long=100, adx_threshold=999.0,
        )
        df = _trending_ohlcv(n=200)
        result = clf.classify(df)
        # ADX < 999 always → CHOP
        assert result.regime == Regime.CHOP
