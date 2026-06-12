"""Signal funnel tracker.

Records every step in the signal pipeline so you can see exactly where
trades are being filtered out.  Attach to any strategy run:

    tracker = SignalFunnelTracker()
    pipeline.run(df, audit_tracker=tracker)
    print(tracker.report())
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict


class RejectionReason:
    """Standard rejection reason constants — extend as needed."""
    REGIME_FAIL = "regime_fail"
    ATR_FLOOR = "atr_floor_fail"
    WHERE_THRESHOLD = "where_threshold_not_met"
    WHEN_THRESHOLD = "when_threshold_not_met"
    NO_OB_IN_ZONE = "no_ob_in_zone"
    RISK_DAILY_LOSS = "risk_daily_loss"
    RISK_DRAWDOWN = "risk_drawdown"
    RISK_COOLDOWN = "risk_cooldown"
    RISK_SIZE = "risk_size_cap"
    RISK_CONCURRENT = "risk_concurrent_positions"


@dataclass
class FunnelCounts:
    bars_processed: int = 0
    sweeps_detected: int = 0
    bos_detected: int = 0
    choch_detected: int = 0
    obs_detected: int = 0
    fvg_detected: int = 0
    displacements_detected: int = 0
    where_signals_active: int = 0   # bars where ≥1 WHERE signal present
    when_signals_active: int = 0    # bars where ≥1 WHEN signal present
    entries_generated: int = 0
    entries_rejected: int = 0
    trades_executed: int = 0


class SignalFunnelTracker:
    """Thread-unsafe (single-run) signal funnel counter.

    Usage:
        tracker = SignalFunnelTracker()
        tracker.record("sweeps_detected", 3)
        tracker.reject(RejectionReason.REGIME_FAIL)
        tracker.record("trades_executed")
        print(tracker.report())
    """

    _VALID_EVENTS = set(FunnelCounts.__dataclass_fields__.keys())

    def __init__(self) -> None:
        self._counts = FunnelCounts()
        self._rejections: Dict[str, int] = defaultdict(int)

    # ── Counting ──────────────────────────────────────────────────────────────

    def record(self, event: str, n: int = 1) -> None:
        """Increment a named funnel counter by n."""
        if event not in self._VALID_EVENTS:
            raise ValueError(f"Unknown event: '{event}'. Valid: {sorted(self._VALID_EVENTS)}")
        setattr(self._counts, event, getattr(self._counts, event) + n)

    def reject(self, reason: str, n: int = 1) -> None:
        """Record n entry rejections with a labelled reason."""
        self._counts.entries_rejected += n
        self._rejections[reason] += n

    # ── Read-only accessors ───────────────────────────────────────────────────

    @property
    def counts(self) -> FunnelCounts:
        return self._counts

    def rejection_breakdown(self) -> Dict[str, int]:
        return dict(self._rejections)

    def conversion_rate(self) -> float:
        """trades_executed / entries_generated (0.0 if no entries generated)."""
        generated = self._counts.entries_generated
        return self._counts.trades_executed / generated if generated > 0 else 0.0

    def summary(self) -> dict:
        return {
            "counts": {k: getattr(self._counts, k) for k in self._VALID_EVENTS},
            "rejection_reasons": self.rejection_breakdown(),
            "conversion_rate": self.conversion_rate(),
        }

    def report(self) -> str:
        c = self._counts
        lines = [
            "=== Signal Funnel Report ===",
            f"  Bars processed:          {c.bars_processed:>8,}",
            f"  Liquidity sweeps:        {c.sweeps_detected:>8,}",
            f"  BOS events:              {c.bos_detected:>8,}",
            f"  CHOCH events:            {c.choch_detected:>8,}",
            f"  OBs detected:            {c.obs_detected:>8,}",
            f"  FVGs detected:           {c.fvg_detected:>8,}",
            f"  Displacements:           {c.displacements_detected:>8,}",
            f"  WHERE signals active:    {c.where_signals_active:>8,}",
            f"  WHEN signals active:     {c.when_signals_active:>8,}",
            "  ─────────────────────────────────",
            f"  Entries generated:       {c.entries_generated:>8,}",
            f"  Entries rejected:        {c.entries_rejected:>8,}",
            f"  Trades executed:         {c.trades_executed:>8,}",
            f"  Conversion rate:         {self.conversion_rate():>8.1%}",
        ]
        if self._rejections:
            lines.append("\n  Rejection breakdown:")
            for reason, count in sorted(self._rejections.items(), key=lambda x: -x[1]):
                lines.append(f"    {reason:<35} {count:>6,}")
        return "\n".join(lines)

    def bottleneck(self) -> str:
        """Return the name of the funnel stage with the largest drop-off."""
        c = self._counts
        stages = [
            ("bars → sweeps",         c.bars_processed,   c.sweeps_detected),
            ("sweeps → choch",         c.sweeps_detected,  c.choch_detected),
            ("choch → where_active",   c.choch_detected,   c.where_signals_active),
            ("where → entries",        c.where_signals_active, c.entries_generated),
            ("entries → trades",       c.entries_generated, c.trades_executed),
        ]
        biggest_drop = max(
            stages,
            key=lambda t: (t[1] - t[2]) if t[1] > 0 else 0,
        )
        return biggest_drop[0]
