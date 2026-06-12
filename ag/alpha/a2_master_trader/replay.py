"""
Convert master-trader trade records to R-multiples for gate evaluation.

R-multiple = direction × price_move / reference_pip
  direction    : +1 for BUY, -1 for SELL
  price_move   : exit_price - entry_price (positive if price went up)
  reference_pip: median(|exit - entry|) across IS trades

Execution-honesty model (declared in A2_MASTER_TRADER_DECISION.md §2):
  - 30-second copy lag approximated by pip-level slippage on entry
  - 1.5 pips round-trip total cost (0.5 slip × 2 + 0.5 commission × 2 ≈ 1.5)
  - PIP_SIZE = 0.10 $/oz  →  cost_in_R = 0.15 / reference_pip

The cost is applied via CostModel so the gate's net-PF check uses honest numbers.
"""
from __future__ import annotations

import statistics

from ag.alpha.a2_master_trader.loader import RawTrade, PIP_SIZE_USD, COPY_LAG_PIPS
from ag.validation.cost_model import CostModel


def compute_reference_pip(is_trades: list[RawTrade]) -> float:
    """Median absolute price movement across IS trades."""
    if not is_trades:
        raise ValueError("IS trades list is empty")
    moves = [abs(t.exit_price - t.entry_price) for t in is_trades]
    return statistics.median(moves)


def trades_to_r_multiples(
    trades: list[RawTrade],
    reference_pip: float,
) -> list[float]:
    """
    Convert trade records to gross R-multiples using the IS reference pip.

    R = direction × (exit - entry) / reference_pip

    Entry slippage (30-second lag approximation) is baked into the cost model,
    not the raw R — so this function returns GROSS R-multiples.
    The CostModel returned by make_cost_model() applies the net adjustment.
    """
    if reference_pip <= 0:
        raise ValueError(f"reference_pip must be positive, got {reference_pip}")
    result = []
    for t in trades:
        direction = 1.0 if t.side.upper() == "BUY" else -1.0
        raw = direction * (t.exit_price - t.entry_price) / reference_pip
        result.append(raw)
    return result


def make_cost_model(reference_pip: float) -> CostModel:
    """
    Execution-honesty CostModel for A2.

    Total cost = COPY_LAG_PIPS × PIP_SIZE_USD / reference_pip  (in R-units)
    Split evenly across spread/commission/slippage for CostModel compatibility.
    """
    total_r = (COPY_LAG_PIPS * PIP_SIZE_USD) / reference_pip
    third = total_r / 3.0
    return CostModel(spread_r=third, commission_r=third, slippage_r=total_r - 2 * third)
