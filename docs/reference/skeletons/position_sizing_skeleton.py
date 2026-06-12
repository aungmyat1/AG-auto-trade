"""
REFERENCE SKELETON — NOT PRODUCTION CODE
=========================================
This file is a reconciliation artefact from the ZIP audit (2026-06-12).

CONFLICT — do NOT integrate:
  This skeleton implements position sizing outside the RiskEngine.
  G4 in `ag/risk/engine.py` already covers position size:
      RiskConfig.max_position_size_pct = 0.005  (0.5% per trade)

  Adding a parallel sizing module would violate CLAUDE.md rule 10:
  "No duplicate subsystems. One implementation per concern, always."

  Use `RiskConfig.max_position_size_pct` and `RiskEngine.validate_entry()` instead.

THRESHOLD CONFLICTS:
  Uploaded skeleton uses base_risk=0.0075 (0.75%), max_risk=0.015 (1.5%).
  Design doc RISK_MODEL_DESIGN.md uses 0.5%–1.5% dynamic range.
  Production G4 hard cap is 0.5%/trade (CLAUDE.md rule 5 / GATE_DECISION.md).
  No sizing variant may exceed 0.5%; the regime scale-up in calculate_size()
  cannot be used as-is — output must still pass RiskEngine.validate_entry().

If you need volatility-adjusted sizing in future, add it as a method on
RiskEngine or RiskConfig — do not create a parallel module.
"""

from typing import Literal


class PositionSizer:
    """
    SKELETON ONLY — see conflict note above.

    Volatility-targeted sizing with regime scaling (from uploaded design doc).
    NOT used in production; G4 guard enforces the hard 0.5%/trade cap.
    Any output from calculate_size() must still pass RiskEngine.validate_entry().
    """

    # Regime multipliers from uploaded design doc (RISK_MODEL_DESIGN.md §2.3)
    _REGIME_SCALE = {
        "strong": 1.5,   # capped at max_risk before use
        "normal": 1.0,
        "weak": 0.67,
    }

    def __init__(
        self,
        base_risk: float = 0.005,    # 0.5% — G4 hard cap; design doc had 0.0075
        max_risk: float = 0.005,     # same cap; design doc had 0.015
        atr_multiplier: float = 1.5,
    ):
        self.base_risk = base_risk
        self.max_risk = max_risk
        self.atr_multiplier = atr_multiplier

    def calculate_size(
        self,
        equity: float,
        stop_atr: float,
        atr_value: float,
        pip_value: float,
        regime: Literal["strong", "normal", "weak"] = "normal",
    ) -> float:
        """
        Returns position size in lots/units (volatility-targeted).

        Formula: (equity * risk_pct) / (stop_atr * atr_value * pip_value)

        Output is advisory — caller must pass through RiskEngine.validate_entry()
        which enforces the hard 0.5%/trade cap regardless of this output.
        """
        scale = self._REGIME_SCALE.get(regime, 1.0)
        risk_pct = min(self.max_risk, self.base_risk * scale)
        risk_amount = equity * risk_pct
        stop_value = stop_atr * atr_value * pip_value
        if stop_value <= 0:
            return 0.0
        return round(risk_amount / stop_value, 2)

    def calculate(
        self,
        account_balance: float,
        atr: float,
        entry_price: float,
        stop_distance: float | None = None,
    ) -> float:
        """Simple ATR-based sizing (no pip_value needed — for futures)."""
        if stop_distance is None:
            stop_distance = self.atr_multiplier * atr
        if stop_distance <= 0 or entry_price <= 0:
            return 0.0
        risk_amount = account_balance * self.base_risk
        return risk_amount / stop_distance
