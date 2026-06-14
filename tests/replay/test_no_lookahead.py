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

# The four detectors that are look-ahead-clean. `liquidity` is excluded here and
# pinned separately below as a documented known defect (LF-1).
CLEAN = [(n, f) for n, f in DETECT_FNS if n != "liquidity"]
CLEAN_IDS = [n for n, _ in CLEAN]
_LIQUIDITY_DETECT = dict(DETECT_FNS)["liquidity"]


@pytest.mark.parametrize("name,detect", DETECT_FNS, ids=IDS)
def test_detector_finds_something(name, detect, structured_df):
    # A vacuous stability test is no test — assert the detector actually fires.
    assert len(detect(structured_df)) >= 1


@pytest.mark.parametrize("name,detect", CLEAN, ids=CLEAN_IDS)
@pytest.mark.parametrize("split", SPLITS)
def test_no_future_leakage(name, detect, split, structured_df):
    assert future_leak_free(detect, structured_df, split), (
        f"{name}: poisoning bars after {split} changed past detections — look-ahead bias"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "LF-1 — LiquidityDetector look-ahead: it keeps a past swing as a liquidity "
        "level only if it clusters with another equal-high drawn from the WHOLE series, "
        "including FUTURE swings (liquidity.py:50-55). Poisoning the future makes a past "
        "pool appear/vanish. Fix: tag the level at its confirmation bar (latest swing in "
        "the cluster) and/or cluster only with bars already seen. Tracked for owner review; "
        "A1 code is not changed during the freeze. When fixed, this test will XPASS and "
        "strict=True will flag it to be un-xfailed."
    ),
)
def test_liquidity_lookahead_known_defect_LF1(structured_df):
    assert future_leak_free(_LIQUIDITY_DETECT, structured_df, 180)


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
