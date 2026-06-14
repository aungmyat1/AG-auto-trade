"""No-look-ahead tests: detections about the past must not change when the
future changes. Includes a deliberately-leaky detector to prove the check
actually CATCHES leakage (a guard that can't fail is worthless).
"""
from __future__ import annotations

import pytest

from ag.alpha.a1_smc_momentum.detectors.base import OrderBlock
from ag.validation.replay_harness import future_leak_free, poison_future

from ._smc_cases import DETECT_FNS, IDS

SPLITS = [120, 180, 240]


@pytest.mark.parametrize("name,detect", DETECT_FNS, ids=IDS)
def test_detector_finds_something(name, detect, structured_df):
    # A vacuous stability test is no test — assert the detector actually fires.
    assert len(detect(structured_df)) >= 1


@pytest.mark.parametrize("name,detect", DETECT_FNS, ids=IDS)
@pytest.mark.parametrize("split", SPLITS)
def test_no_future_leakage(name, detect, split, structured_df):
    # All five detectors must be look-ahead-clean. (liquidity's LF-1 future-cluster
    # leak was fixed: it now clusters only with past swings — see liquidity.py.)
    assert future_leak_free(detect, structured_df, split), (
        f"{name}: poisoning bars after {split} changed past detections — look-ahead bias"
    )


def test_poison_future_leaves_past_bars_untouched(structured_df):
    split = 150
    poisoned = poison_future(structured_df, split)
    pd_testing_equal = structured_df.iloc[: split + 1].equals(poisoned.iloc[: split + 1])
    assert pd_testing_equal, "poisoning must not alter bars <= split"
    # and it must actually change the future
    assert not structured_df.iloc[split + 1:].equals(poisoned.iloc[split + 1:])


# ── meta-sentinel: a detector that peeks at the future MUST be flagged ─────────

class _LeakyDetector:
    """Labels bar i using the LAST (future) bar's close — textbook leakage."""

    def detect(self, df):
        out = []
        future_close = float(df["close"].iloc[-1])  # <-- reads the future
        for i in range(2, len(df) - 2):
            if float(df["close"].iloc[i]) < future_close:
                out.append(
                    OrderBlock(
                        direction="bullish",
                        high=float(df["high"].iloc[i]),
                        low=float(df["low"].iloc[i]),
                        bar_index=i,
                        strength=0.5,
                    )
                )
        return out


def test_leaky_detector_is_caught(structured_df):
    leaky = _LeakyDetector()
    # If the framework can't catch this, every other no-lookahead test is meaningless.
    assert future_leak_free(leaky.detect, structured_df, 240) is False
