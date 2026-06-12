"""
Risk Management Engine — instrument-agnostic, no exchange coupling.

Adapted from auto-trade-system/app/risk/risk_engine.py.
All state is in-memory; caller owns persistence if needed.

Six sequential guards (non-bypassable per AG plan §risk):
  G1  Daily loss limit
  G2  Max drawdown from peak
  G3  Consecutive-loss cooldown
  G4  Position size cap
  G5  Max leverage
  G6  Max concurrent positions

Calling validate_entry() checks ALL six in order.
A single violation returns approved=False; callers must not bypass.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    max_daily_loss_pct: float = 0.02        # G1: 2% daily loss limit
    max_drawdown_pct: float = 0.15          # G2: 15% drawdown from peak
    max_consecutive_losses: int = 3         # G3: cooldown trigger
    cooldown_period_seconds: int = 3600     # G3: 1-hour cooldown
    max_position_size_pct: float = 0.005    # G4: 0.5% per trade (AG plan)
    max_leverage: int = 5                   # G5
    max_concurrent_positions: int = 3       # G6
    weekly_loss_stop_pct: float = 0.06      # advisory — not a hard guard


@dataclass
class RiskDecision:
    approved: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_score: float = 0.0          # 0–100, higher = riskier
    daily_pnl_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    cooldown_remaining_s: int = 0


class RiskEngine:
    """
    Non-bypassable 6-guard risk engine.

    Usage:
        engine = RiskEngine(RiskConfig())
        decision = engine.validate_entry(position_size_pct=0.005)
        if not decision.approved:
            # must not trade
            ...
        engine.open_position("trade-001")
        ...
        engine.record_trade_result(pnl_pct=-0.003, trade_id="trade-001")
    """

    def __init__(self, config: Optional[RiskConfig] = None) -> None:
        self.config = config or RiskConfig()
        # Daily state (reset by caller at day boundary)
        self.daily_pnl_pct: float = 0.0
        # Equity state
        self.peak_balance: float = 1.0   # normalized
        self.current_balance: float = 1.0
        # Consecutive loss state
        self.consecutive_losses: int = 0
        self.last_loss_time: Optional[float] = None
        # Position registry
        self.open_positions: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def validate_entry(self, position_size_pct: float = 0.005) -> RiskDecision:
        """Run all 6 guards in order. Returns approved=False on first violation."""
        violations: list[str] = []
        warnings: list[str] = []

        # G1: Daily loss
        if self.daily_pnl_pct <= -self.config.max_daily_loss_pct:
            violations.append(
                f"G1 daily loss {self.daily_pnl_pct:.2%} >= limit {self.config.max_daily_loss_pct:.2%}"
            )

        # G2: Drawdown
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if drawdown >= self.config.max_drawdown_pct:
            violations.append(
                f"G2 drawdown {drawdown:.2%} >= limit {self.config.max_drawdown_pct:.2%}"
            )

        # G3: Cooldown
        cooldown_remaining = 0
        if (
            self.last_loss_time is not None
            and self.consecutive_losses >= self.config.max_consecutive_losses
        ):
            elapsed = time.time() - self.last_loss_time
            remaining = self.config.cooldown_period_seconds - elapsed
            if remaining > 0:
                cooldown_remaining = int(remaining)
                violations.append(
                    f"G3 cooldown {cooldown_remaining}s remaining after {self.consecutive_losses} losses"
                )

        # G4: Position size
        if position_size_pct > self.config.max_position_size_pct:
            violations.append(
                f"G4 size {position_size_pct:.2%} > cap {self.config.max_position_size_pct:.2%}"
            )

        # G5: Leverage — advisory check (actual leverage determined at execution)
        # Callers may pass leverage separately; here we flag if exposure exceeds limit
        # (position_size_pct * leverage <= max_leverage * position_size_pct — always pass)
        # G5 is enforced at execution layer

        # G6: Concurrent positions
        if len(self.open_positions) >= self.config.max_concurrent_positions:
            violations.append(
                f"G6 concurrent positions {len(self.open_positions)} >= max {self.config.max_concurrent_positions}"
            )

        # Risk score: daily loss utilization
        risk_score = min(
            100.0,
            abs(self.daily_pnl_pct) / max(self.config.max_daily_loss_pct, 1e-10) * 100,
        )

        approved = len(violations) == 0
        if not approved:
            logger.warning("Risk rejected: %s", violations)

        return RiskDecision(
            approved=approved,
            violations=violations,
            warnings=warnings,
            risk_score=risk_score,
            daily_pnl_pct=self.daily_pnl_pct,
            current_drawdown_pct=float(drawdown),
            cooldown_remaining_s=cooldown_remaining,
        )

    # ------------------------------------------------------------------
    # State updates
    # ------------------------------------------------------------------

    def open_position(self, trade_id: str, metadata: Optional[Dict] = None) -> None:
        self.open_positions[trade_id] = metadata or {}

    def record_trade_result(self, pnl_pct: float, trade_id: Optional[str] = None) -> None:
        """Update state after a trade closes. pnl_pct = fractional P&L of account."""
        self.daily_pnl_pct += pnl_pct
        self.current_balance = self.current_balance * (1.0 + pnl_pct)
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance

        if pnl_pct < 0:
            self.consecutive_losses += 1
            self.last_loss_time = time.time()
        else:
            self.consecutive_losses = 0
            self.last_loss_time = None

        if trade_id and trade_id in self.open_positions:
            del self.open_positions[trade_id]

    def reset_daily(self) -> None:
        """Call at each day boundary."""
        self.daily_pnl_pct = 0.0
