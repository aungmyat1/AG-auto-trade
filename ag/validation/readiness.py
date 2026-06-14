"""Trading Readiness Gate System (TRGS) — Decision Aggregator.

Answers ONE question: CAN THIS SYSTEM TRADE REAL MONEY RIGHT NOW?

Produces a 6-state ladder status and a machine-readable JSON report.
Pre-registered thresholds: ag/validation/lock_before_look/TRGS_THRESHOLDS.md

Architecture:
    ValidationGate (gate.py) → ROBUST / READ / FRAGILE    (strategy edge)
    EdgeValidator  (edge_validator.py) → PASS / FAIL       (vs random baseline)
    TRGSDecisionEngine (this module) → 6-state status      (deployment readiness)

Kill switch: READY_FOR_LIVE requires manual_override = True.
The agent NEVER sets manual_override. Only the OWNER does.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List, Optional

from ag.validation.gate import GateResult
from ag.validation.edge_validator import EdgeResult


class ReadinessStatus(str, Enum):
    NOT_READY = "NOT_READY"
    READY_FOR_BACKTEST = "READY_FOR_BACKTEST"
    READY_FOR_PAPER = "READY_FOR_PAPER"
    READY_FOR_SHADOW = "READY_FOR_SHADOW"
    READY_FOR_LIVE = "READY_FOR_LIVE"
    BLOCKED = "BLOCKED"


@dataclass
class TRGSReport:
    status: ReadinessStatus
    gate_verdict: str                    # ROBUST / READ / FRAGILE / NOT_RUN
    n_trades: int
    max_drawdown: float
    edge_passed: bool
    edge_outperformance_pct: float
    manual_override: bool
    blockers: List[str]
    promoters: List[str]                 # conditions that advanced the tier
    checks_passed: int
    checks_failed: int
    alpha_pf: float
    timestamp_utc: str                   # ISO-8601; caller must provide

    def to_json(self, indent: int = 2) -> str:
        d = {
            "status": self.status.value,
            "gate_verdict": self.gate_verdict,
            "n_trades": self.n_trades,
            "max_drawdown": round(self.max_drawdown, 6),
            "edge_passed": self.edge_passed,
            "edge_outperformance_pct": round(self.edge_outperformance_pct * 100, 2),
            "manual_override": self.manual_override,
            "blockers": self.blockers,
            "promoters": self.promoters,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "alpha_pf": round(self.alpha_pf, 6),
            "timestamp_utc": self.timestamp_utc,
            "thresholds": {
                "paper_min_trades": TRGSDecisionEngine.PAPER_N,
                "shadow_min_trades": TRGSDecisionEngine.SHADOW_N,
                "shadow_max_drawdown": TRGSDecisionEngine.SHADOW_MAX_DD,
                "edge_min_outperformance": TRGSDecisionEngine.EDGE_MIN_OUTPERFORMANCE,
            },
        }
        return json.dumps(d, indent=indent)

    def report(self) -> str:
        lines = [
            f"{'=' * 60}",
            f"  TRADING READINESS GATE SYSTEM (TRGS)",
            f"  STATUS: {self.status.value}",
            f"{'=' * 60}",
            f"  Gate verdict:    {self.gate_verdict}  (n={self.n_trades})",
            f"  Max drawdown:    {self.max_drawdown:.1%}  (shadow limit: {TRGSDecisionEngine.SHADOW_MAX_DD:.0%})",
            f"  Edge vs random:  {self.edge_outperformance_pct:+.1%}  {'PASS' if self.edge_passed else 'FAIL'}",
            f"  Manual override: {self.manual_override}",
            f"  Checks: {self.checks_passed} passed / {self.checks_failed} failed",
        ]
        if self.promoters:
            lines.append(f"\n  Promoters (why tier advanced):")
            for p in self.promoters:
                lines.append(f"    ✓ {p}")
        if self.blockers:
            lines.append(f"\n  Blockers (why tier is limited):")
            for b in self.blockers:
                lines.append(f"    ✗ {b}")
        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


class TRGSDecisionEngine:
    """Aggregate gate + edge results into a single deployment readiness decision.

    Tier ladder (each tier requires ALL prior tiers):
        NOT_READY          → gate not run or FRAGILE
        READY_FOR_BACKTEST → infrastructure valid (look-ahead tests pass, risk engine tests pass)
        READY_FOR_PAPER    → gate READ + edge passes (n >= PAPER_N, gross PF > 1)
        READY_FOR_SHADOW   → gate ROBUST + n >= SHADOW_N + max_dd < SHADOW_MAX_DD + edge passes
        READY_FOR_LIVE     → READY_FOR_SHADOW + manual_override = True
        BLOCKED            → any hard violation (supersedes all tiers)

    Pre-registered in: ag/validation/lock_before_look/TRGS_THRESHOLDS.md
    """

    # Pre-registered thresholds (TRGS_THRESHOLDS.md — do not change after data exposure)
    PAPER_N: int = 50                       # READ floor from GATE_DECISION.md
    SHADOW_N: int = 500                     # stricter than gate ROBUST (200)
    SHADOW_MAX_DD: float = 0.10             # stricter than gate ROBUST (0.15)
    EDGE_MIN_OUTPERFORMANCE: float = 0.10   # 10% above random baseline

    def evaluate(
        self,
        gate_result: GateResult,
        edge_result: EdgeResult,
        timestamp_utc: str,
        manual_override: bool = False,
        hard_blockers: Optional[List[str]] = None,
    ) -> TRGSReport:
        """Map gate + edge results to a TRGSReport.

        Args:
            gate_result:     Output of ValidationGate.run().
            edge_result:     Output of EdgeValidator.validate().
            timestamp_utc:   ISO-8601 timestamp string (caller provides — no datetime in pure logic).
            manual_override: True only when OWNER has explicitly enabled live trading.
                             The agent never sets this to True.
            hard_blockers:   Optional list of pre-detected hard violations
                             (e.g. look-ahead test failures, replay violations).
                             Any non-empty list forces BLOCKED status.
        """
        blockers: List[str] = list(hard_blockers or [])
        promoters: List[str] = []

        checks_passed = gate_result.passed_checks
        checks_failed = len(gate_result.failed_checks)
        n = gate_result.n_trades
        max_dd = _extract_max_dd(gate_result)
        alpha_pf = _extract_pf(gate_result)

        # ── BLOCKED (hard gate — supersedes everything) ──────────────────────
        if blockers:
            return TRGSReport(
                status=ReadinessStatus.BLOCKED,
                gate_verdict=gate_result.verdict,
                n_trades=n,
                max_drawdown=max_dd,
                edge_passed=edge_result.passed,
                edge_outperformance_pct=edge_result.outperformance_pct,
                manual_override=manual_override,
                blockers=blockers,
                promoters=[],
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                alpha_pf=alpha_pf,
                timestamp_utc=timestamp_utc,
            )

        # ── NOT_READY ────────────────────────────────────────────────────────
        if gate_result.verdict == "FRAGILE":
            blockers.append(f"gate verdict = FRAGILE (n={n}, floor not passed)")
            return _report(ReadinessStatus.NOT_READY, gate_result, edge_result,
                           manual_override, blockers, promoters, alpha_pf, timestamp_utc)

        # ── READY_FOR_BACKTEST ───────────────────────────────────────────────
        # Infrastructure prerequisite — if we have a gate result at all, the
        # backtest pipeline ran cleanly.  Look-ahead tests must also be green
        # (checked externally; non-green would appear as a hard_blocker above).
        promoters.append("gate ran successfully (backtest pipeline operational)")

        if gate_result.verdict == "FRAGILE":
            return _report(ReadinessStatus.READY_FOR_BACKTEST, gate_result, edge_result,
                           manual_override, blockers, promoters, alpha_pf, timestamp_utc)

        # ── READY_FOR_PAPER ──────────────────────────────────────────────────
        # Requires: READ or ROBUST verdict + edge validation passes.
        paper_ok = gate_result.verdict in ("READ", "ROBUST") and n >= self.PAPER_N
        if not paper_ok:
            blockers.append(f"n={n} < {self.PAPER_N} (READ floor not reached)")

        if not edge_result.passed:
            blockers.append(
                f"edge {edge_result.outperformance_pct:+.1%} < {self.EDGE_MIN_OUTPERFORMANCE:.0%} "
                f"vs random baseline"
            )

        if not (paper_ok and edge_result.passed):
            return _report(ReadinessStatus.READY_FOR_BACKTEST, gate_result, edge_result,
                           manual_override, blockers, promoters, alpha_pf, timestamp_utc)

        promoters.append(f"gate READ/ROBUST with n={n} >= {self.PAPER_N}")
        promoters.append(f"edge beats random by {edge_result.outperformance_pct:+.1%}")

        # ── READY_FOR_SHADOW ─────────────────────────────────────────────────
        # Requires: ROBUST verdict + n >= 500 + max_dd < 10%.
        shadow_blockers: List[str] = []

        if gate_result.verdict != "ROBUST":
            shadow_blockers.append(f"gate verdict = {gate_result.verdict} (need ROBUST)")
        if n < self.SHADOW_N:
            shadow_blockers.append(f"n={n} < {self.SHADOW_N} (shadow trade minimum)")
        if max_dd >= self.SHADOW_MAX_DD:
            shadow_blockers.append(
                f"max_dd={max_dd:.1%} >= {self.SHADOW_MAX_DD:.0%} (shadow drawdown limit)"
            )

        if shadow_blockers:
            blockers.extend(shadow_blockers)
            return _report(ReadinessStatus.READY_FOR_PAPER, gate_result, edge_result,
                           manual_override, blockers, promoters, alpha_pf, timestamp_utc)

        promoters.append(f"gate ROBUST with n={n} >= {self.SHADOW_N}")
        promoters.append(f"max_dd={max_dd:.1%} < {self.SHADOW_MAX_DD:.0%}")

        # ── READY_FOR_LIVE ───────────────────────────────────────────────────
        # Requires: READY_FOR_SHADOW + explicit manual_override from OWNER.
        if not manual_override:
            blockers.append("manual_override not set — OWNER must explicitly enable live trading")
            return _report(ReadinessStatus.READY_FOR_SHADOW, gate_result, edge_result,
                           manual_override, blockers, promoters, alpha_pf, timestamp_utc)

        promoters.append("manual_override = True (OWNER approved)")
        return _report(ReadinessStatus.READY_FOR_LIVE, gate_result, edge_result,
                       manual_override, blockers, promoters, alpha_pf, timestamp_utc)


# ── Private helpers ──────────────────────────────────────────────────────────

def _report(
    status: ReadinessStatus,
    gate_result: GateResult,
    edge_result: EdgeResult,
    manual_override: bool,
    blockers: List[str],
    promoters: List[str],
    alpha_pf: float,
    timestamp_utc: str,
) -> TRGSReport:
    return TRGSReport(
        status=status,
        gate_verdict=gate_result.verdict,
        n_trades=gate_result.n_trades,
        max_drawdown=_extract_max_dd(gate_result),
        edge_passed=edge_result.passed,
        edge_outperformance_pct=edge_result.outperformance_pct,
        manual_override=manual_override,
        blockers=blockers,
        promoters=promoters,
        checks_passed=gate_result.passed_checks,
        checks_failed=len(gate_result.failed_checks),
        alpha_pf=alpha_pf,
        timestamp_utc=timestamp_utc,
    )


def _extract_max_dd(gate_result: GateResult) -> float:
    for c in gate_result.checks:
        if "DD" in c.name or "drawdown" in c.name.lower():
            return c.value
    return 0.0


def _extract_pf(gate_result: GateResult) -> float:
    for c in gate_result.checks:
        if "PF" in c.name and "net" in c.name.lower():
            return c.value
        if "PF" in c.name and "gross" in c.name.lower():
            return c.value
    return 0.0
