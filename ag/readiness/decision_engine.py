"""
Trading Readiness Gate System (TRGS) — the single decision: may capital be risked?

This is a *capital-deployment firewall*, not a strategy. It does not reimplement
the validation gate, the risk engine, or the replay checks — it COMPOSES them
(one implementation per concern, GROUND_TRUTH rule 10) into one fail-closed
answer.

Hard invariants:
  • Fail-closed: the default state is NOT_READY/BLOCKED; readiness must be earned.
  • Any hard-required validator FAIL ⇒ BLOCKED.
  • READY_FOR_LIVE additionally requires an explicit owner override; the engine
    NEVER enables live trading and never sets LIVE_TRADING (that stays an owner-
    only manual flip — GROUND_TRUTH hard rule 1).
  • Execution-dependent validators (system health, infra resilience) report
    NOT_AVAILABLE until the Phase-D execution layer exists; that caps readiness
    below LIVE by design.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"   # cannot be assessed yet (e.g. no execution layer)
    NOT_RUN = "NOT_RUN"


class ReadinessState(str, Enum):
    NOT_READY = "NOT_READY"
    READY_FOR_BACKTEST = "READY_FOR_BACKTEST"
    READY_FOR_PAPER = "READY_FOR_PAPER"
    READY_FOR_SHADOW = "READY_FOR_SHADOW"
    READY_FOR_LIVE = "READY_FOR_LIVE"
    BLOCKED = "BLOCKED"


@dataclass
class ValidatorResult:
    name: str
    status: CheckStatus
    detail: str = ""
    evidence: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == CheckStatus.PASS

    @property
    def failed(self) -> bool:
        return self.status == CheckStatus.FAIL


@dataclass
class ReadinessReport:
    state: ReadinessState
    results: list[ValidatorResult]
    manual_override: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def can_trade_live(self) -> bool:
        return self.state == ReadinessState.READY_FOR_LIVE

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "can_trade_live": self.can_trade_live,
            "manual_override": self.manual_override,
            "reasons": self.reasons,
            "validators": [
                {"name": r.name, "status": r.status.value, "detail": r.detail,
                 "evidence": r.evidence}
                for r in self.results
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def summary(self) -> str:
        lines = [f"TRGS STATE: {self.state.value}",
                 f"can_trade_live: {self.can_trade_live}", "-" * 56]
        for r in self.results:
            icon = {"PASS": "PASS", "FAIL": "FAIL", "NOT_AVAILABLE": "N/A ",
                    "NOT_RUN": "----"}[r.status.value]
            lines.append(f"  [{icon}] {r.name}: {r.detail}")
        if self.reasons:
            lines.append("Reasons:")
            lines += [f"  - {r}" for r in self.reasons]
        return "\n".join(lines)


class ReadinessGate:
    """Aggregates validator results into one readiness state. Fail-closed.

    Hard-required (must PASS for any forward progress):
        backtest · replay · risk · edge
    Execution-dependent (needed only for LIVE; NOT_AVAILABLE pre-Phase-D):
        system_health · infra
    """

    REQUIRED = ("backtest", "replay", "risk", "edge")
    EXECUTION = ("system_health", "infra")

    def evaluate(
        self, results: list[ValidatorResult], *, manual_override: bool = False
    ) -> ReadinessReport:
        by_name = {r.name: r for r in results}
        reasons: list[str] = []

        # 1) Any hard FAIL anywhere ⇒ BLOCKED (look-ahead, risk breach, etc.).
        hard_fails = [r for r in results if r.failed]
        if hard_fails:
            reasons = [f"{r.name} FAILED: {r.detail}" for r in hard_fails]
            return ReadinessReport(ReadinessState.BLOCKED, results, manual_override, reasons)

        # 2) Required validators must all have run and passed.
        required = [by_name.get(n) for n in self.REQUIRED]
        if any(r is None or r.status == CheckStatus.NOT_RUN for r in required):
            missing = [n for n in self.REQUIRED
                       if by_name.get(n) is None or by_name[n].status == CheckStatus.NOT_RUN]
            reasons.append(f"required validators not run: {', '.join(missing)}")

        replay_ok = by_name.get("replay") and by_name["replay"].ok
        risk_ok = by_name.get("risk") and by_name["risk"].ok
        backtest_ok = by_name.get("backtest") and by_name["backtest"].ok
        edge_ok = by_name.get("edge") and by_name["edge"].ok

        # 3) No ROBUST backtest yet, but the harness itself is trustworthy
        #    (replay clean + risk verified) ⇒ safe to RUN a backtest.
        if not backtest_ok:
            if replay_ok and risk_ok:
                reasons.append("no ROBUST verdict yet — harness verified, run the gate")
                return ReadinessReport(ReadinessState.READY_FOR_BACKTEST, results,
                                       manual_override, reasons)
            reasons.append("backtest not ROBUST and harness not yet verified")
            return ReadinessReport(ReadinessState.NOT_READY, results, manual_override, reasons)

        # 4) All required pass. Climb the ladder, gated by execution availability.
        if not (replay_ok and risk_ok and edge_ok):
            return ReadinessReport(ReadinessState.NOT_READY, results, manual_override, reasons)

        execution = [by_name.get(n) for n in self.EXECUTION]
        execution_pass = all(r is not None and r.ok for r in execution)
        execution_unavailable = any(
            r is None or r.status == CheckStatus.NOT_AVAILABLE for r in execution
        )

        if execution_unavailable:
            reasons.append("execution layer not available (Phase D locked) — paper only")
            return ReadinessReport(ReadinessState.READY_FOR_PAPER, results,
                                   manual_override, reasons)

        if execution_pass and not manual_override:
            reasons.append("all gates pass — owner override required before LIVE (kill switch)")
            return ReadinessReport(ReadinessState.READY_FOR_SHADOW, results,
                                   manual_override, reasons)

        if execution_pass and manual_override:
            return ReadinessReport(ReadinessState.READY_FOR_LIVE, results,
                                   manual_override, reasons)

        return ReadinessReport(ReadinessState.NOT_READY, results, manual_override, reasons)
