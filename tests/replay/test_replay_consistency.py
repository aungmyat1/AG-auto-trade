"""Replay-harness behaviour: it exposes only history up to the current bar,
is deterministic, and never hands a callback a future bar.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.validation.replay_harness import ReplayHarness

from ._smc_cases import DETECT_FNS, IDS, make_structured_ohlcv


def test_window_never_contains_future(structured_df):
    harness = ReplayHarness(structured_df, warmup=10)
    for i, hist in harness.stream():
        assert len(hist) == i + 1                       # exactly bars 0..i
        assert hist.index[-1] == structured_df.index[i]  # last bar is the current one
        assert hist.index.max() <= structured_df.index[i]


def test_stream_covers_every_bar_from_warmup(structured_df):
    harness = ReplayHarness(structured_df, warmup=10)
    seen = [i for i, _ in harness.stream()]
    assert seen == list(range(9, len(structured_df)))


def test_replay_is_deterministic():
    df = make_structured_ohlcv(seed=11)
    run1 = [(i, len(h)) for i, h in ReplayHarness(df, warmup=5).stream()]
    run2 = [(i, len(h)) for i, h in ReplayHarness(df, warmup=5).stream()]
    assert run1 == run2


def test_callback_cannot_mutate_source(structured_df):
    harness = ReplayHarness(structured_df, warmup=10)
    before = structured_df.copy()

    def vandal(i, hist):
        hist.iloc[:, :] = -999.0  # try to corrupt — operates on a copy

    harness.run(vandal)
    assert structured_df.equals(before)


@pytest.mark.parametrize("name,detect", DETECT_FNS, ids=IDS)
def test_replay_window_detections_match_batch_past(name, detect, structured_df):
    # Detecting on the final replay window (whole series) equals the batch run:
    # the harness adds no distortion, it just controls *when* bars are visible.
    *_, (last_i, last_hist) = list(ReplayHarness(structured_df, warmup=10).stream())
    assert detect(last_hist) == detect(structured_df.iloc[: last_i + 1])
