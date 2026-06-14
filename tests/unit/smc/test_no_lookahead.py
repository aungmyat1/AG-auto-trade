"""No-look-ahead / no-repainting regression tests for all SMC detectors.

PHASE 4 coverage (verification ladder): proves that appending future bars
to a DataFrame cannot change detections on bars that were already present.

Pattern for each detector:
  1. Run on df[:N]      → get reference detections on bars 0..N-1
  2. Run on df[:N+M]    → get detections on the extended set
  3. Assert: every detection with bar_index < (N - confirmation_lag) is
     present and unchanged in the extended run.

"confirmation_lag" accounts for bars that need future closes to confirm
a pattern (e.g. swing highs need n bars after the pivot — those near the
boundary are legitimately unconfirmed and may gain or lose detections as
more bars arrive).  We only assert on detections safely before the boundary.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.detectors.liquidity import LiquidityDetector
from ag.alpha.a1_smc_momentum.detectors.order_block import OrderBlockDetector
from ag.alpha.a1_smc_momentum.detectors.fvg import FairValueGapDetector
from ag.alpha.a1_smc_momentum.detectors.bos_choch import BosChochDetector


# ── Shared fixture ────────────────────────────────────────────────────────────

_POOL_SIZE = 200  # generate once; slice to n so bars 0..n-1 are identical across calls


def _make_ohlcv(n: int, seed: int = 42) -> pd.DataFrame:
    """Deterministic OHLCV sliced from a fixed-size pool.

    Critically: bars 0..n-1 are IDENTICAL regardless of n, because all series
    are generated at full _POOL_SIZE before slicing.  This lets look-ahead tests
    compare df[:N] vs df[:N+M] without data-generation artifacts.
    """
    rng = np.random.default_rng(seed)
    close = 1800.0 + np.cumsum(rng.normal(0, 3, _POOL_SIZE))
    high = close + rng.uniform(1, 5, _POOL_SIZE)
    low = close - rng.uniform(1, 5, _POOL_SIZE)
    open_ = close + rng.normal(0, 1, _POOL_SIZE)
    volume = rng.integers(1000, 5000, _POOL_SIZE).astype(float)
    return pd.DataFrame({
        "open": open_[:n], "high": high[:n], "low": low[:n],
        "close": close[:n], "volume": volume[:n],
    })


EXTENSION = 20   # extra bars appended for the look-ahead test


# ── LiquidityDetector ─────────────────────────────────────────────────────────

class TestLiquidityNoLookahead:
    """Swing-high/low detection uses n bars before AND after the pivot.
    Boundary lag = swing_lookback bars from the end of the window.
    """

    def test_no_repaint_on_extension(self):
        det = LiquidityDetector(swing_lookback=3, atr_window=5, cluster_atr_mult=0.3)
        n = 80
        lag = det.swing_lookback   # confirmed swings require n bars after pivot

        df_base = _make_ohlcv(n)
        df_ext = _make_ohlcv(n + EXTENSION)

        base_results = det.detect(df_base)
        ext_results = det.detect(df_ext)

        # Only compare detections safely before the confirmation boundary
        safe_limit = n - lag
        base_safe = {r.bar_index for r in base_results if r.bar_index < safe_limit}
        ext_safe = {r.bar_index for r in ext_results if r.bar_index < safe_limit}

        assert base_safe == ext_safe, (
            f"LiquidityDetector repainted: base had {sorted(base_safe)}, "
            f"extended had {sorted(ext_safe)} (safe limit={safe_limit})"
        )

    def test_sweep_status_monotonic(self):
        """Once sweep_confirmed=True, adding future bars must not un-confirm it.

        It IS valid for a level to go False→True when extended data provides a
        sweep event.  The look-ahead bug would be the reverse: True→False.
        """
        det = LiquidityDetector(swing_lookback=2, atr_window=5)
        n = 60
        lag = det.swing_lookback

        df_base = _make_ohlcv(n, seed=7)
        df_ext = _make_ohlcv(n + EXTENSION, seed=7)

        safe_limit = n - lag
        base_swept = {
            r.bar_index: r.sweep_confirmed
            for r in det.detect(df_base) if r.bar_index < safe_limit
        }
        ext_swept = {
            r.bar_index: r.sweep_confirmed
            for r in det.detect(df_ext) if r.bar_index < safe_limit
        }

        for idx, confirmed in base_swept.items():
            assert idx in ext_swept, f"Level at bar {idx} disappeared after extension"
            if confirmed:
                assert ext_swept[idx], (
                    f"Sweep at bar {idx} was confirmed in base but un-confirmed "
                    f"in extended — look-ahead bug (True→False is illegal)"
                )


# ── OrderBlockDetector ────────────────────────────────────────────────────────

class TestOrderBlockNoLookahead:
    """OB displacement uses only past bars (high/low up to bar i-1).
    No confirmation lag — OB bar_index < N is safe to compare."""

    def test_no_repaint_on_extension(self):
        det = OrderBlockDetector(displacement_atr_mult=0.8, atr_window=5, lookback=3)
        n = 80

        df_base = _make_ohlcv(n)
        df_ext = _make_ohlcv(n + EXTENSION)

        base_idx = {r.bar_index for r in det.detect(df_base)}
        ext_idx = {r.bar_index for r in det.detect(df_ext) if r.bar_index < n}

        assert base_idx == ext_idx, (
            f"OrderBlockDetector repainted: base={sorted(base_idx)}, "
            f"extended (bars<{n})={sorted(ext_idx)}"
        )

    def test_ob_properties_unchanged_after_extension(self):
        """OB direction, high, low, strength must be stable."""
        det = OrderBlockDetector(displacement_atr_mult=0.8, atr_window=5, lookback=3)
        n = 80

        df_base = _make_ohlcv(n, seed=13)
        df_ext = _make_ohlcv(n + EXTENSION, seed=13)

        base_obs = {r.bar_index: r for r in det.detect(df_base)}
        ext_obs = {r.bar_index: r for r in det.detect(df_ext) if r.bar_index < n}

        for idx, ob in base_obs.items():
            assert idx in ext_obs, f"OB at bar {idx} disappeared after extension"
            assert ext_obs[idx].direction == ob.direction
            assert ext_obs[idx].high == pytest.approx(ob.high)
            assert ext_obs[idx].low == pytest.approx(ob.low)


# ── FairValueGapDetector ──────────────────────────────────────────────────────

class TestFVGNoLookahead:
    """FVG is a 3-candle pattern using bars i-2, i-1, i — all past or current.
    bar_index = i-1 (the middle candle). No confirmation lag."""

    def test_no_repaint_on_extension(self):
        det = FairValueGapDetector(min_size_atr=0.3, atr_window=5)
        n = 80

        df_base = _make_ohlcv(n)
        df_ext = _make_ohlcv(n + EXTENSION)

        base_idx = {(r.bar_index, r.direction) for r in det.detect(df_base)}
        ext_idx = {
            (r.bar_index, r.direction)
            for r in det.detect(df_ext) if r.bar_index < n
        }

        assert base_idx == ext_idx, (
            f"FVGDetector repainted: base={sorted(base_idx)}, "
            f"extended (bars<{n})={sorted(ext_idx)}"
        )

    def test_fvg_size_unchanged_after_extension(self):
        det = FairValueGapDetector(min_size_atr=0.3, atr_window=5)
        n = 80

        df_base = _make_ohlcv(n, seed=17)
        df_ext = _make_ohlcv(n + EXTENSION, seed=17)

        base_fvgs = {
            (r.bar_index, r.direction): r.size_atr for r in det.detect(df_base)
        }
        ext_fvgs = {
            (r.bar_index, r.direction): r.size_atr
            for r in det.detect(df_ext) if r.bar_index < n
        }

        for key, size in base_fvgs.items():
            assert key in ext_fvgs, f"FVG {key} disappeared after extension"
            assert ext_fvgs[key] == pytest.approx(size), (
                f"FVG {key} size changed: {size} → {ext_fvgs[key]}"
            )


# ── BosChochDetector ──────────────────────────────────────────────────────────

class TestBosChochNoLookahead:
    """BosChoch explicitly uses only swings confirmed before bar i-n (see detector
    code: `relevant_sh = [h for h in sh_indices if h < i - n]`).
    Boundary lag = swing_lookback bars from end of the window."""

    def test_no_repaint_on_extension(self):
        det = BosChochDetector(swing_lookback=3, atr_window=5)
        n = 100
        lag = det.swing_lookback

        df_base = _make_ohlcv(n)
        df_ext = _make_ohlcv(n + EXTENSION)

        safe_limit = n - lag
        base_idx = {r.bar_index for r in det.detect(df_base) if r.bar_index < safe_limit}
        ext_idx = {r.bar_index for r in det.detect(df_ext) if r.bar_index < safe_limit}

        assert base_idx == ext_idx, (
            f"BosChochDetector repainted: base={sorted(base_idx)}, "
            f"extended={sorted(ext_idx)} (safe limit={safe_limit})"
        )

    def test_break_type_stable_after_extension(self):
        """BOS / CHOCH type and direction must not flip when future bars arrive."""
        det = BosChochDetector(swing_lookback=3, atr_window=5)
        n = 100
        lag = det.swing_lookback
        safe_limit = n - lag

        df_base = _make_ohlcv(n, seed=23)
        df_ext = _make_ohlcv(n + EXTENSION, seed=23)

        base_breaks = {
            r.bar_index: (r.type, r.direction)
            for r in det.detect(df_base) if r.bar_index < safe_limit
        }
        ext_breaks = {
            r.bar_index: (r.type, r.direction)
            for r in det.detect(df_ext) if r.bar_index < safe_limit
        }

        for idx, (btype, bdir) in base_breaks.items():
            assert idx in ext_breaks, f"Break at bar {idx} disappeared"
            assert ext_breaks[idx] == (btype, bdir), (
                f"Break at bar {idx}: was {(btype, bdir)}, now {ext_breaks[idx]}"
            )
