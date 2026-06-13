"""Synthetic OHLCV generators for CI tests (B4).

These produce GC/MGC/6E-shaped DataFrames without any API calls, covering
CME session hours, realistic price ranges, and controllable defects for
integrity-check testing.

All returned DataFrames match the contract expected by DatabentoLoader and
check_ohlcv: UTC DatetimeIndex, columns [open, high, low, close, volume].
"""
from __future__ import annotations

import random
from typing import Optional

import pandas as pd
import numpy as np


# ── Price anchors (approximate 2023 ranges) ───────────────────────────────────

_PRICE_ANCHOR = {"GC": 1950.0, "MGC": 1950.0, "6E": 1.08}
_TICK = {"GC": 0.10, "MGC": 0.10, "6E": 0.00005}
_VOLUME_BASE = {"GC": 120_000, "MGC": 40_000, "6E": 80_000}


def make_ohlcv(
    symbol: str = "GC",
    timeframe: str = "1h",
    n_bars: int = 500,
    start: str = "2023-01-02",
    seed: int = 42,
    with_duplicates: bool = False,
    with_ohlc_violation: bool = False,
    with_gap: bool = False,
    with_nan: bool = False,
) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame that mimics CME futures data.

    Defect flags allow integrity-check tests to inject specific failures:
        with_duplicates       Insert a duplicate timestamp at bar 50
        with_ohlc_violation   Set high < low at bar 100
        with_gap              Insert a 20-bar gap after bar 200
        with_nan              Insert NaN in close at bar 150
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    anchor = _PRICE_ANCHOR.get(symbol, 1000.0)
    tick = _TICK.get(symbol, 0.01)
    vol_base = _VOLUME_BASE.get(symbol, 50_000)

    freq = "1h" if timeframe == "1h" else "1min"
    # CME GC/6E trade nearly 23h/day — use hourly to keep fixtures small
    timestamps = pd.date_range(start=start, periods=n_bars, freq=freq, tz="UTC")

    # Simple random-walk price series
    log_returns = np_rng.normal(0, 0.002, n_bars)
    closes = anchor * np.exp(np.cumsum(log_returns))

    opens = np.roll(closes, 1)
    opens[0] = closes[0]

    spreads = np.abs(np_rng.normal(0, 0.003, n_bars)) * anchor + tick
    highs = np.maximum(opens, closes) + spreads * 0.5
    lows = np.minimum(opens, closes) - spreads * 0.5
    volumes = (np_rng.poisson(vol_base, n_bars)).astype(float)

    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes},
        index=timestamps,
    )
    df.index.name = "timestamp"

    # ── Inject defects ────────────────────────────────────────────────────────
    if with_duplicates and len(df) > 51:
        df = pd.concat([df.iloc[:51], df.iloc[50:51], df.iloc[51:]])

    if with_ohlc_violation and len(df) > 100:
        df.iloc[100, df.columns.get_loc("high")] = df.iloc[100]["low"] - 1.0

    if with_gap and len(df) > 220:
        df = pd.concat([df.iloc[:200], df.iloc[220:]])

    if with_nan and len(df) > 150:
        df.iloc[150, df.columns.get_loc("close")] = float("nan")

    df.attrs["symbol"] = symbol
    df.attrs["timeframe"] = timeframe
    return df


def make_gc_1h(n_bars: int = 500, **kwargs) -> pd.DataFrame:
    return make_ohlcv("GC", "1h", n_bars=n_bars, **kwargs)


def make_mgc_1h(n_bars: int = 500, **kwargs) -> pd.DataFrame:
    return make_ohlcv("MGC", "1h", n_bars=n_bars, **kwargs)


def make_6e_1h(n_bars: int = 500, **kwargs) -> pd.DataFrame:
    return make_ohlcv("6E", "1h", n_bars=n_bars, **kwargs)


def make_gc_1m(n_bars: int = 1000, **kwargs) -> pd.DataFrame:
    return make_ohlcv("GC", "1m", n_bars=n_bars, **kwargs)


def save_fixture(df: pd.DataFrame, path) -> None:
    """Write a synthetic fixture to parquet (used to seed the cache in tests)."""
    import pathlib
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=True)
