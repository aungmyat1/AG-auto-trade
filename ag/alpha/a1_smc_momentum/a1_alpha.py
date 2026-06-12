"""A1 SMC Momentum Alpha Module.

Entry logic: liquidity sweep → structure break (CHOCH/BOS) → entry.
Optional gates: OB zone, FVG, displacement (add one at a time; measure
each filter's impact on trade count before keeping it).

Design principle — cure the 1-trade-per-363-pair-day failure mode:
  Multi-OB tracking: all unmitigated order blocks across history are
  kept in _active_obs.  Entry checks ALL unmitigated OBs, not just the
  last one.  A price revisit to OB[i] 30 bars after it formed is valid.

Phase B MVP config = PipelineConfig(sweep=True, choch=True, ob=False, fvg=False)
  This is a NEW alpha ID (A0_MVP) — not the locked A1 spec.
  The locked A1 spec (A1_SMC_MOMENTUM_DECISION.md) requires ≥3-of-4 WHERE
  + ≥2-of-3 WHEN.  Never conflate the two.

NOT ready for live trading. Returns is_ready()=False until ROBUST gate verdict.
"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from ag.alpha.base import AlphaModule, SignalProposal
from ag.alpha.a1_smc_momentum.detectors.base import OrderBlock
from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig, PipelineResult, SmcPipeline
from ag.validation.signal_audit import SignalFunnelTracker
from ag.validation.signal_audit.tracker import RejectionReason


class A1SmcMomentum(AlphaModule):
    """SMC momentum: sweep → CHOCH/BOS → (optional OB/FVG/displacement).

    Attach an audit_tracker to get a full funnel report after any run.
    Call reset() between independent backtest runs.
    """

    alpha_id = "A1"
    description = "SMC context filter + momentum entry (sweep + CHOCH)"

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        audit_tracker: Optional[SignalFunnelTracker] = None,
    ) -> None:
        self._config = config or PipelineConfig()   # default: sweep+choch only
        self._pipeline = SmcPipeline(self._config)
        self._audit = audit_tracker or SignalFunnelTracker()
        # Multi-OB tracker — accumulates across propose() calls, never just latest
        self._active_obs: List[OrderBlock] = []

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def audit(self) -> SignalFunnelTracker:
        return self._audit

    def propose(self, market_data: dict) -> Optional[SignalProposal]:
        """Generate a trade proposal.

        market_data must contain:
            "df": pd.DataFrame with [open, high, low, close, volume] columns,
                  chronological order (newest row last), minimum 10 rows.

        Returns SignalProposal if all enabled conditions are met, else None.
        Every rejection is logged to the audit tracker.
        """
        df: pd.DataFrame = market_data.get("df")
        if df is None or len(df) < 10:
            return None

        result: PipelineResult = self._pipeline.run(df, audit_tracker=self._audit)

        # ── Multi-OB tracking (accumulate + expire mitigated) ──────────────
        if result.obs:
            self._active_obs.extend(result.obs)
        # Mark mitigated in-place using the detector (re-check against latest df)
        if self._active_obs and self._config.ob:
            from ag.alpha.a1_smc_momentum.detectors import OrderBlockDetector
            det = OrderBlockDetector(atr_window=self._config.atr_window)
            self._active_obs = det.mark_mitigated(self._active_obs, df)
        self._active_obs = [ob for ob in self._active_obs if not ob.mitigated]

        # ── Phase B MVP: sweep required ────────────────────────────────────
        if not result.sweeps:
            self._audit.reject(RejectionReason.NO_SWEEP)
            return None

        # ── Structure break: CHOCH preferred; BOS accepted ─────────────────
        struct_breaks = result.choch_events or result.bos_events
        if not struct_breaks:
            self._audit.reject(RejectionReason.NO_CHOCH)
            return None

        most_recent = struct_breaks[-1]

        # ── Optional OB filter ──────────────────────────────────────────────
        if self._config.ob:
            current_price = float(df["close"].iloc[-1])
            matching_ob = self._find_ob_at_price(current_price)
            if matching_ob is None:
                self._audit.reject(RejectionReason.NO_OB_UNMITIGATED)
                return None

        # ── Optional FVG filter ─────────────────────────────────────────────
        if self._config.fvg and not result.fvgs:
            self._audit.reject(RejectionReason.NO_FVG)
            return None

        # ── Optional displacement filter ────────────────────────────────────
        if self._config.displacement and not result.displacements:
            self._audit.reject(RejectionReason.NO_DISPLACEMENT)
            return None

        # ── All conditions met ──────────────────────────────────────────────
        self._audit.record("entries_generated")
        direction = most_recent.direction   # 'bullish' | 'bearish'
        n_sweeps = len(result.sweeps)
        return SignalProposal(
            direction="long" if direction == "bullish" else "short",
            confidence=min(1.0, n_sweeps * 0.25 + most_recent.strength * 0.75),
            alpha_id=self.alpha_id,
            entry_rationale=(
                f"{most_recent.type}({direction}) after {n_sweeps} sweep(s) "
                f"[config={self._config.label()}]"
            ),
            # Placeholder distances — real values come from OB/ATR in production
            stop_distance_pct=0.5,
            target_distance_pct=1.0,
        )

    def is_ready(self) -> bool:
        """False until a ROBUST gate verdict exists for A1."""
        return False

    def reset(self) -> None:
        """Clear OB history and audit state for a new independent run."""
        self._active_obs = []
        self._audit = SignalFunnelTracker()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _find_ob_at_price(self, price: float) -> Optional[OrderBlock]:
        """Return the most recent active OB whose range contains price."""
        for ob in reversed(self._active_obs):
            if ob.low <= price <= ob.high:
                return ob
        return None
