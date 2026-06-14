"""Shared synthetic data + detector registry for replay/look-ahead tests.

Lenient detector params (small ATR windows / lookbacks) so the five detectors
fire on short synthetic series — the same approach the per-detector unit tests
use. The exact detections don't matter here; what matters is that they are
non-trivial and that they don't depend on the future.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ag.alpha.a1_smc_momentum.detectors.bos_choch import BosChochDetector
from ag.alpha.a1_smc_momentum.detectors.displacement import DisplacementDetector
from ag.alpha.a1_smc_momentum.detectors.fvg import FairValueGapDetector
from ag.alpha.a1_smc_momentum.detectors.liquidity import LiquidityDetector
from ag.alpha.a1_smc_momentum.detectors.order_block import OrderBlockDetector


def make_structured_ohlcv(n: int = 300, seed: int = 7) -> pd.DataFrame:
    """Deterministic OHLCV with alternating trends (swings) + injected sharp
    displacement/gap candles, so every detector finds something."""
    rng = np.random.default_rng(seed)
    o_l, h_l, l_l, c_l, v_l = [], [], [], [], []
    price = 1800.0
    for i in range(n):
        drift = 0.8 if (i // 25) % 2 == 0 else -0.8        # trend segments → swings
        o = price
        c = price + rng.normal(drift, 2.0)
        hi = max(o, c) + abs(rng.normal(0, 1.0))
        lo = min(o, c) - abs(rng.normal(0, 1.0))
        if i in (88, 89, 90):          # bullish displacement + gap up + order block
            c = o + 16.0; hi = c + 0.6; lo = o + 0.4
        elif i in (200, 201, 202):     # bearish displacement + gap down
            c = o - 16.0; lo = c - 0.6; hi = o - 0.4
        o_l.append(o); h_l.append(hi); l_l.append(lo); c_l.append(c)
        v_l.append(float(rng.integers(1000, 5000)))
        price = c
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(
        {"open": o_l, "high": h_l, "low": l_l, "close": c_l, "volume": v_l}, index=idx
    )


def detector_cases() -> list[tuple[str, object]]:
    """(name, detector) with lenient params so each fires on synthetic data."""
    return [
        ("order_block", OrderBlockDetector(displacement_atr_mult=0.5, atr_window=5, lookback=3)),
        ("fvg", FairValueGapDetector(min_size_atr=0.2, atr_window=5)),
        ("liquidity", LiquidityDetector(swing_lookback=3, cluster_atr_mult=0.3, atr_window=5)),
        ("bos_choch", BosChochDetector(swing_lookback=3, atr_window=5)),
        ("displacement", DisplacementDetector(atr_mult=0.8, atr_window=5)),
    ]


CASES = detector_cases()
IDS = [name for name, _ in CASES]
DETECT_FNS = [(name, det.detect) for name, det in CASES]
