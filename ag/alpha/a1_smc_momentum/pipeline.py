"""Composable SMC strategy pipeline.

Start with the MVP (sweep=True, choch=True, all others False).
Add one filter at a time.  Every filter must prove it improves expectancy
WITHOUT destroying trade count before the next filter is added.

Phase B MVP (minimum viable — needs its own lock-before-look spec):
    pipeline = SmcPipeline(PipelineConfig(sweep=True, choch=True))

Phase C step 1 (after MVP proves edge):
    pipeline = SmcPipeline(PipelineConfig(sweep=True, choch=True, ob=True))

IMPORTANT: Changing any PipelineConfig boolean changes the strategy definition.
Every new config combination must be registered as a new alpha trial BEFORE
running the gate (lock-before-look rule — GATE_DECISION.md §5).

DO NOT modify the locked A1 spec (A1_SMC_MOMENTUM_DECISION.md).
Phase B / Phase C combinations are NEW alpha IDs, not modifications of A1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from .detectors import (
    BosChochDetector,
    Displacement,
    DisplacementDetector,
    FairValueGapDetector,
    FairValueGap,
    LiquidityDetector,
    LiquidityLevel,
    OrderBlock,
    OrderBlockDetector,
    StructureBreak,
)
from ag.validation.signal_audit import SignalFunnelTracker


@dataclass
class PipelineConfig:
    # ── Toggle each component ────────────────────────────────────────────────
    sweep: bool = True   # LiquidityDetector — find swept highs/lows
    choch: bool = True   # BosChochDetector — find CHOCH events (trend reversal signal)
    ob: bool = False     # OrderBlockDetector — require price in OB zone
    fvg: bool = False    # FairValueGapDetector — require FVG confluence
    displacement: bool = False  # DisplacementDetector — require displacement candle

    # ── Shared detector params ───────────────────────────────────────────────
    swing_lookback: int = 5
    atr_window: int = 14
    ob_displacement_mult: float = 1.5
    fvg_min_size_atr: float = 0.5

    def active_components(self) -> List[str]:
        return [k for k in ("sweep", "choch", "ob", "fvg", "displacement") if getattr(self, k)]

    def label(self) -> str:
        """Short string label for logging, e.g. 'sweep+choch'."""
        return "+".join(self.active_components()) or "empty"


@dataclass
class PipelineResult:
    sweeps: List[LiquidityLevel] = field(default_factory=list)
    bos_events: List[StructureBreak] = field(default_factory=list)
    choch_events: List[StructureBreak] = field(default_factory=list)
    obs: List[OrderBlock] = field(default_factory=list)
    fvgs: List[FairValueGap] = field(default_factory=list)
    displacements: List[Displacement] = field(default_factory=list)


class SmcPipeline:
    """Run enabled SMC detectors and populate a PipelineResult.

    The pipeline is DATA-ONLY — it does not make entry decisions.
    Entry logic lives in the AlphaModule that owns this pipeline.
    Attach a SignalFunnelTracker to record counts for audit reporting.
    """

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()
        self._build()

    def _build(self) -> None:
        cfg = self.config
        n = cfg.swing_lookback
        w = cfg.atr_window

        self._liquidity: Optional[LiquidityDetector] = (
            LiquidityDetector(swing_lookback=n, atr_window=w) if cfg.sweep else None
        )
        self._bos_choch: Optional[BosChochDetector] = (
            BosChochDetector(swing_lookback=n, atr_window=w) if cfg.choch else None
        )
        self._ob: Optional[OrderBlockDetector] = (
            OrderBlockDetector(
                displacement_atr_mult=cfg.ob_displacement_mult,
                atr_window=w,
            )
            if cfg.ob
            else None
        )
        self._fvg: Optional[FairValueGapDetector] = (
            FairValueGapDetector(min_size_atr=cfg.fvg_min_size_atr, atr_window=w)
            if cfg.fvg
            else None
        )
        self._displacement: Optional[DisplacementDetector] = (
            DisplacementDetector(atr_window=w) if cfg.displacement else None
        )

    def run(
        self,
        df: pd.DataFrame,
        audit_tracker: Optional[SignalFunnelTracker] = None,
    ) -> PipelineResult:
        """Run all enabled detectors on df.

        Args:
            df: OHLCV DataFrame with columns [open, high, low, close, volume].
            audit_tracker: optional tracker; if provided, counts are recorded.

        Returns:
            PipelineResult with detected events for each enabled component.
        """
        result = PipelineResult()

        if audit_tracker:
            audit_tracker.record("bars_processed", len(df))

        if self._liquidity is not None:
            levels = self._liquidity.detect(df)
            result.sweeps = [lv for lv in levels if lv.sweep_confirmed]
            if audit_tracker:
                audit_tracker.record("sweeps_detected", len(result.sweeps))

        if self._bos_choch is not None:
            breaks = self._bos_choch.detect(df)
            result.bos_events = [b for b in breaks if b.type == "BOS"]
            result.choch_events = [b for b in breaks if b.type == "CHOCH"]
            if audit_tracker:
                audit_tracker.record("bos_detected", len(result.bos_events))
                audit_tracker.record("choch_detected", len(result.choch_events))

        if self._ob is not None:
            result.obs = self._ob.detect(df)
            if audit_tracker:
                audit_tracker.record("obs_detected", len(result.obs))

        if self._fvg is not None:
            result.fvgs = self._fvg.detect(df)
            if audit_tracker:
                audit_tracker.record("fvg_detected", len(result.fvgs))

        if self._displacement is not None:
            result.displacements = self._displacement.detect(df)
            if audit_tracker:
                audit_tracker.record("displacements_detected", len(result.displacements))

        return result
