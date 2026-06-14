"""
Realistic cost model for intraday futures trading (GC/MGC, 6E).

Costs are expressed in R-multiples and subtracted from each trade's gross PnL.
A winning +2R trade with 0.15R total cost → +1.85R net.
A losing -1R trade with 0.15R total cost → -1.15R net.
Cost is always paid (it's a round-trip drag on every trade).

Gate check: PF_NET = profit_factor(apply(trades_r)) > 1.25
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostModel:
    """
    Per-trade cost in R-multiples.

    Default values are conservative estimates for Databento CME futures:
      spread    : 0.05R  (1 tick spread / average stop distance)
      commission: 0.05R  (round-trip exchange + clearing)
      slippage  : 0.05R  (fill slippage at signal, not limit)
    """
    spread_r: float = 0.05
    commission_r: float = 0.05
    slippage_r: float = 0.05

    @property
    def total_r(self) -> float:
        return self.spread_r + self.commission_r + self.slippage_r

    def apply(self, trades_r: list[float]) -> list[float]:
        """Subtract round-trip cost from every trade."""
        c = self.total_r
        return [t - c for t in trades_r]

    def profit_factor_net(self, trades_r: list[float]) -> float:
        net = self.apply(trades_r)
        wins = sum(t for t in net if t > 0)
        losses = abs(sum(t for t in net if t < 0))
        if losses == 0:
            return float("inf") if wins > 0 else 1.0
        return wins / losses

    def with_shock(
        self,
        spread_mult: float = 1.5,
        slippage_mult: float = 2.0,
    ) -> "CostModel":
        """Return a copy with spread and slippage scaled. Commission is unchanged.

        Use for stress-testing: does the strategy survive wider spreads and
        worse fills? Typical shock: spread_mult=1.5, slippage_mult=2.0.
        """
        return CostModel(
            spread_r=self.spread_r * spread_mult,
            commission_r=self.commission_r,
            slippage_r=self.slippage_r * slippage_mult,
        )

    @classmethod
    def for_gc(cls) -> "CostModel":
        """GC (Gold futures, 100 oz) — slightly wider spread than FX."""
        return cls(spread_r=0.07, commission_r=0.05, slippage_r=0.06)

    @classmethod
    def for_mgc(cls) -> "CostModel":
        """MGC (Micro Gold futures, 10 oz = 1/10 GC).

        Spread and slippage in R are identical to GC — same underlying, same tick
        ($0.10/oz), so spread_ticks / stop_ticks is unchanged by contract size.
        Commission, however, is a fixed $/contract that does NOT shrink to 1/10 for
        micros (typical micro round-trip ≈ $1.0–1.2 vs ≈ $5 on GC, on a 10×-smaller
        notional). Net effect: ~2× the relative commission drag of GC.

        Conservative estimate; refine with the actual broker schedule on the WORKER.
        commission_r = 0.10 assumes ~$1.0 round-trip over a ~10-tick ($10) MGC stop.
        """
        return cls(spread_r=0.07, commission_r=0.10, slippage_r=0.06)

    @classmethod
    def for_6e(cls) -> "CostModel":
        """6E (Euro FX futures) — tighter spread."""
        return cls(spread_r=0.04, commission_r=0.04, slippage_r=0.04)
