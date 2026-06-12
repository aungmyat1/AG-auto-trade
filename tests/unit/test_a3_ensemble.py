"""Unit tests for A3Ensemble alpha module."""
from __future__ import annotations


from ag.alpha.a3_ensemble.a3 import A3Ensemble, _W_SMC, _W_REGIME, _W_MASTER, _THRESHOLD
from ag.alpha.base import SignalProposal


def _proposal(direction: str = "long", confidence: float = 0.8, alpha_id: str = "A1") -> SignalProposal:
    return SignalProposal(
        direction=direction,
        confidence=confidence,
        alpha_id=alpha_id,
        entry_rationale="test",
        stop_distance_pct=0.5,
        target_distance_pct=1.0,
    )


class TestA3Weights:
    def test_weights_sum_to_one(self):
        assert abs(_W_SMC + _W_REGIME + _W_MASTER - 1.0) < 1e-9

    def test_threshold_is_locked(self):
        assert _THRESHOLD == 0.75

    def test_locked_weights(self):
        assert _W_SMC == 0.4
        assert _W_REGIME == 0.3
        assert _W_MASTER == 0.3


class TestA3IsReady:
    def test_not_ready(self):
        alpha = A3Ensemble()
        assert alpha.is_ready() is False

    def test_alpha_id(self):
        assert A3Ensemble.alpha_id == "A3"


class TestA3Propose:
    def test_both_none_returns_none(self):
        alpha = A3Ensemble()
        result = alpha.propose({"a1_proposal": None, "a2_proposal": None})
        assert result is None

    def test_conflicting_directions_returns_none(self):
        alpha = A3Ensemble()
        result = alpha.propose({
            "a1_proposal": _proposal("long", 0.9),
            "a2_proposal": _proposal("short", 0.9),
        })
        assert result is None

    def test_low_score_returns_none(self):
        alpha = A3Ensemble()
        # Both very low confidence → score < 0.75
        result = alpha.propose({
            "a1_proposal": _proposal("long", 0.1),
            "a2_proposal": _proposal("long", 0.1),
        })
        assert result is None

    def test_high_score_returns_proposal(self):
        alpha = A3Ensemble()
        # Both high confidence, no df (regime=0.5 default)
        # score = 0.4*0.95 + 0.3*0.5 + 0.3*0.95 = 0.38 + 0.15 + 0.285 = 0.815 > 0.75
        result = alpha.propose({
            "a1_proposal": _proposal("long", 0.95),
            "a2_proposal": _proposal("long", 0.95),
        })
        assert result is not None
        assert result.direction == "long"
        assert result.alpha_id == "A3"
        assert result.confidence > 0.75

    def test_only_a1_signal_uses_a2_zero(self):
        alpha = A3Ensemble()
        # a2=None → a2_conf=0.0
        # score = 0.4*0.9 + 0.3*0.5 + 0.3*0.0 = 0.36 + 0.15 + 0.0 = 0.51 < 0.75 → None
        result = alpha.propose({
            "a1_proposal": _proposal("long", 0.9),
            "a2_proposal": None,
        })
        assert result is None

    def test_direction_inherited_from_a1(self):
        alpha = A3Ensemble()
        result = alpha.propose({
            "a1_proposal": _proposal("short", 0.95),
            "a2_proposal": _proposal("short", 0.95),
        })
        assert result is not None
        assert result.direction == "short"

    def test_stop_and_target_set(self):
        alpha = A3Ensemble()
        result = alpha.propose({
            "a1_proposal": _proposal("long", 0.95),
            "a2_proposal": _proposal("long", 0.95),
        })
        assert result is not None
        assert result.stop_distance_pct == 0.5
        assert result.target_distance_pct == 1.0
