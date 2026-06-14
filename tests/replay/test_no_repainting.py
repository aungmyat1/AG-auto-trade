"""No-repainting tests: a concept confirmed on a prefix df[:k] must still exist,
unchanged, when more bars arrive. Mutable state (mitigation) may evolve — that
is forward information, not a repaint, and is excluded from concept identity.
"""
from __future__ import annotations

import pytest

from ag.validation.replay_harness import concept_key, repaint_free

from ._smc_cases import CASES, DETECT_FNS, IDS

SPLITS = [80, 130, 190, 250]


@pytest.mark.parametrize("name,detect", DETECT_FNS, ids=IDS)
def test_detector_does_not_repaint(name, detect, structured_df):
    assert repaint_free(detect, structured_df, SPLITS), (
        f"{name}: a detection present on a prefix disappeared/changed on the full series"
    )


@pytest.mark.parametrize("name,detect", DETECT_FNS, ids=IDS)
def test_growing_history_only_adds_or_mitigates(name, detect, structured_df):
    # Across two prefixes k1 < k2, every concept confirmed by k1 survives to k2.
    k1, k2 = 150, 220
    buffer = 5
    early = {concept_key(o) for o in detect(structured_df.iloc[:k1])
             if o.bar_index <= k1 - buffer}
    later = {concept_key(o) for o in detect(structured_df.iloc[:k2])}
    assert early <= later, f"{name}: confirmed concepts were repainted as bars grew"


def test_concept_key_ignores_mitigation():
    from ag.alpha.a1_smc_momentum.detectors.base import OrderBlock
    a = OrderBlock(direction="bullish", high=10.0, low=9.0, bar_index=5, strength=0.6,
                   mitigated=False)
    b = OrderBlock(direction="bullish", high=10.0, low=9.0, bar_index=5, strength=0.6,
                   mitigated=True)
    # same formation, different mitigation state → same identity
    assert concept_key(a) == concept_key(b)
