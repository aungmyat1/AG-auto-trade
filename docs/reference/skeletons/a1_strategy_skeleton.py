# REFERENCE SKELETON ONLY — do not import or run
# Source: strategy.py upload 2026-06-12
#
# CONFLICTS / ISSUES:
#   1. Imports from 'smc_implementation_skeletons.*' — wrong path.
#      Production detectors: ag/alpha/a1_smc_momentum/detectors/
#   2. Imports PositionSizer — doesn't exist; covered by RiskEngine G4.
#   3. risk_per_trade = 0.0075 — conflicts with locked 0.5% (0.005).
#   4. obs[-3:] — only checks last 3 OBs. Production a1_alpha.py tracks
#      all unmitigated OBs to prevent 1-trade-per-363-pair-days failure.
#   5. Multi-timeframe (H4/H1/M15) — not in locked A1 spec.
#      Needs a new lock-before-look spec before using.
#
# PRODUCTION VERSION: ag/alpha/a1_smc_momentum/a1_alpha.py
#
# WHAT'S WORTH EXTRACTING (for future Phase C work):
#   - OB+FVG alignment check (aligned_fvg logic) — valid confluence idea
#   - ATR-based stop/target — already in a1_alpha.py as placeholder

from typing import Literal, Optional
from dataclasses import dataclass
import pandas as pd

# These imports are intentionally wrong — do not copy to production
# from smc_implementation_skeletons.order_block_detector import OrderBlockDetector
# from ag.risk.position_sizing import PositionSizer


@dataclass
class TradeSignal:
    direction: Literal["long", "short"]
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    concepts_used: list


class A1SMCMomentum_SKELETON:
    """Reference skeleton only. Production class: A1SmcMomentum in a1_alpha.py."""

    def __init__(self, risk_per_trade: float = 0.0075):  # NOTE: locked value is 0.005
        pass

    def generate_signal(
        self,
        h4_df: pd.DataFrame,
        h1_df: pd.DataFrame,
        m15_df: pd.DataFrame,
        equity: float,
    ) -> Optional[TradeSignal]:
        # 1. Higher timeframe bias (H4)
        # structure = self.structure_detector.detect(h4_df)
        # bias = structure[-1].direction

        # 2. H1 Order Block + FVG confluence
        # obs = self.ob_detector.detect(h1_df)
        # fvgs = self.fvg_detector.detect(h1_df)
        #
        # for ob in obs[-3:]:  # NOTE: production checks ALL unmitigated OBs
        #     if bias == ob.direction:
        #         aligned_fvg = any(...)
        #         if aligned_fvg:
        #             return TradeSignal(...)
        return None
