"""
Alpha module interface — all alpha modules implement AlphaModule.

Three alpha modules compete through ONE gate (Phase 2):
  A1  SMC-filter + momentum/delta entry  (Phase 1)
  A2  Master-trader copy (SignalStart)   (Phase 1)
  A3  Ensemble (0.4*smc + 0.3*regime + 0.3*master > 0.75)  (Phase 1)

No alpha gets primacy by assertion — each must clear the full robustness gate.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SignalProposal:
    direction: str           # 'long' | 'short' | 'flat'
    confidence: float        # 0.0 – 1.0
    alpha_id: str            # 'A1' | 'A2' | 'A3'
    entry_rationale: str     # human-readable explanation
    stop_distance_pct: float # stop distance as % of price
    target_distance_pct: float
    instrument: str = ""
    timeframe: str = ""


class AlphaModule(ABC):
    """
    Interface for all alpha modules.

    Modules should NOT be deployed until is_ready() returns True,
    which requires a ROBUST gate verdict on >= 200 net trades.
    """

    alpha_id: str
    description: str

    @abstractmethod
    def propose(self, market_data: dict) -> Optional[SignalProposal]:
        """
        Generate a trade proposal given current market data.
        Returns None if no signal (flat).
        """

    @abstractmethod
    def is_ready(self) -> bool:
        """
        True only if this module has cleared the robustness gate.
        Must return False until gate.verdict == 'ROBUST'.
        Callers must check this before routing live orders.
        """

    @classmethod
    def gate_not_cleared(cls) -> "AlphaModule":
        """Sentinel stub for a module awaiting gate clearance."""
        return _NotReadyModule(cls.alpha_id if hasattr(cls, "alpha_id") else "unknown")


class _NotReadyModule(AlphaModule):
    """Placeholder — gate not cleared. Returns None on every propose()."""

    def __init__(self, alpha_id: str) -> None:
        self.alpha_id = alpha_id
        self.description = f"{alpha_id}: gate not cleared"

    def propose(self, market_data: dict) -> None:
        return None

    def is_ready(self) -> bool:
        return False
