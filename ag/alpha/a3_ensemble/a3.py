"""
A3 Ensemble alpha module.

Combines confidence scores from A1 (SMC-filter+momentum), regime classifier,
and A2 (master-trader copy) into a single weighted score. Fires when score > 0.75.

Weights are PRE-REGISTERED in GATE_DECISION.md:
    A3 = 0.4 * smc_confidence + 0.3 * regime_score + 0.3 * master_confidence > 0.75

These weights must NOT be tuned after any alpha has seen data. Every tuning
attempt adds 1 to the --n-trials count in the Deflated Sharpe calculation.

Status: NOT TESTED — is_ready() returns False until ROBUST gate verdict.
Build order: A1 gated → A2 gated → A3 built and gated.
"""
from __future__ import annotations

from typing import Optional

from ag.alpha.base import AlphaModule, SignalProposal
from ag.regime.classifier import RegimeClassifier, RegimeResult


# Pre-registered weights — from GATE_DECISION.md. Do not tune.
_W_SMC = 0.4
_W_REGIME = 0.3
_W_MASTER = 0.3
_THRESHOLD = 0.75


class A3Ensemble(AlphaModule):
    """
    Ensemble of A1 + regime + A2.

    BLOCKED until:
      1. A1 has a gate verdict (ROBUST or READ)
      2. A2 has a gate verdict (current: READ)
      3. A3 itself clears the gate on GC data

    propose() returns None until both component alphas expose their
    confidence scores via market_data['a1_proposal'] and market_data['a2_proposal'].
    """

    alpha_id = "A3"
    description = "Ensemble: 0.4*SMC + 0.3*regime + 0.3*master > 0.75"

    def __init__(self, regime_classifier: Optional[RegimeClassifier] = None) -> None:
        self._regime = regime_classifier or RegimeClassifier()

    def propose(self, market_data: dict) -> Optional[SignalProposal]:
        """
        Expects market_data to contain:
            'df'           : pd.DataFrame with OHLCV
            'a1_proposal'  : SignalProposal | None from A1SmcMomentum
            'a2_proposal'  : SignalProposal | None from A2MasterTrader
        Returns a SignalProposal if ensemble score > 0.75, else None.
        """
        a1 = market_data.get("a1_proposal")
        a2 = market_data.get("a2_proposal")
        df = market_data.get("df")

        # Need at least one component firing in the same direction
        if a1 is None and a2 is None:
            return None

        # Determine ensemble direction (majority or A1 if alone)
        a1_dir = a1.direction if a1 is not None else None
        a2_dir = a2.direction if a2 is not None else None

        if a1_dir and a2_dir and a1_dir != a2_dir:
            return None  # conflicting signals — no trade

        direction = a1_dir or a2_dir

        # Regime score: map regime to [0.0, 1.0]
        regime_score = 0.5  # neutral default when df unavailable
        if df is not None and len(df) >= 20:
            try:
                regime_result: RegimeResult = self._regime.classify(df)
                regime_score = _regime_to_score(regime_result, direction)
            except Exception:
                regime_score = 0.5

        smc_conf = a1.confidence if a1 is not None else 0.0
        master_conf = a2.confidence if a2 is not None else 0.0

        score = _W_SMC * smc_conf + _W_REGIME * regime_score + _W_MASTER * master_conf

        if score <= _THRESHOLD:
            return None

        return SignalProposal(
            direction=direction,
            confidence=score,
            alpha_id=self.alpha_id,
            entry_rationale=(
                f"ensemble={score:.3f} > {_THRESHOLD} "
                f"(smc={smc_conf:.2f}, regime={regime_score:.2f}, master={master_conf:.2f})"
            ),
            stop_distance_pct=0.5,
            target_distance_pct=1.0,
        )

    def is_ready(self) -> bool:
        return False  # NOT TESTED — gate not cleared

    def reset(self) -> None:
        pass


def _regime_to_score(result: RegimeResult, direction: Optional[str]) -> float:
    """Convert regime classification to a confidence contribution."""
    from ag.regime.classifier import Regime
    regime = result.regime
    size_mult = result.size_multiplier

    # EXPANSION = best for trend following; CHOP = worst
    if regime == Regime.EXPANSION:
        base = 0.85
    elif regime == Regime.NORMAL:
        base = 0.65
    elif regime == Regime.COMPRESSION:
        base = 0.40
    else:  # CHOP
        base = 0.20

    # EMA slope alignment bonus
    if direction == "long" and result.ema50_slope_pct > 0:
        base = min(1.0, base + 0.10)
    elif direction == "short" and result.ema50_slope_pct < 0:
        base = min(1.0, base + 0.10)

    return base * size_mult
