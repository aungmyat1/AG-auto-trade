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

THRESHOLD CONFLICT:
  Skeleton uses base_risk_pct = 0.01 (1.0% per trade).
  Production G4 cap is 0.5% per trade (CLAUDE.md rule 5 / GATE_DECISION.md).
  The skeleton threshold cannot be used.

If you need volatility-adjusted sizing in future, add it as a method on
RiskEngine or RiskConfig — do not create a parallel module.
"""


class PositionSizer:
    """
    SKELETON ONLY — see conflict note above.

    Volatility-adjusted position sizing using ATR.
    Not used in production; G4 guard handles size enforcement.
    """

    def __init__(
        self,
        base_risk_pct: float = 0.005,   # 0.5% — matches G4; original had 0.01
        max_position_pct: float = 0.02,
        atr_multiplier: float = 1.5,
    ):
        self.base_risk_pct = base_risk_pct
        self.max_position_pct = max_position_pct
        self.atr_multiplier = atr_multiplier

    def calculate(
        self,
        account_balance: float,
        atr: float,
        entry_price: float,
        stop_distance: float | None = None,
    ) -> float:
        """
        Returns suggested position size in base units.
        Caller must still pass through RiskEngine.validate_entry().
        """
        if stop_distance is None:
            stop_distance = self.atr_multiplier * atr

        if stop_distance <= 0 or entry_price <= 0:
            return 0.0

        risk_amount = account_balance * self.base_risk_pct
        size = risk_amount / stop_distance
        max_size = (account_balance * self.max_position_pct) / entry_price
        return min(size, max_size)
