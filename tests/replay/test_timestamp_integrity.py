"""Timestamp integrity: the harness refuses non-monotonic or duplicate
timestamps, and never exposes a bar timestamped later than the current one.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.validation.replay_harness import FutureAccessError, ReplayHarness

from ._smc_cases import make_structured_ohlcv


def test_rejects_non_monotonic_timestamps(structured_df):
    bad = structured_df.copy()
    idx = bad.index.to_list()
    idx[10], idx[11] = idx[11], idx[10]  # swap two timestamps → out of order
    bad.index = pd.DatetimeIndex(idx)
    with pytest.raises(FutureAccessError):
        ReplayHarness(bad)


def test_rejects_duplicate_timestamps(structured_df):
    bad = structured_df.copy()
    idx = bad.index.to_list()
    idx[20] = idx[19]  # duplicate
    bad.index = pd.DatetimeIndex(idx)
    with pytest.raises(FutureAccessError):
        ReplayHarness(bad)


def test_streamed_windows_are_monotonic(structured_df):
    harness = ReplayHarness(structured_df, warmup=10)
    for i, hist in harness.stream():
        assert hist.index.is_monotonic_increasing
        # nothing newer than the current bar is ever visible
        assert hist.index.max() == structured_df.index[i]


def test_accepts_timestamp_column_form():
    df = make_structured_ohlcv(seed=3).reset_index().rename(columns={"index": "timestamp"})
    # timestamp as a column (not index) — still validated, must not raise
    ReplayHarness(df, warmup=5)
