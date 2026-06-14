"""Trading Readiness Gate System (TRGS) — a capital-deployment firewall.

Answers one question: may this system risk real money right now? It composes the
locked subsystems (ValidationGate, RiskEngine, replay_harness) into one
fail-closed decision. It never enables live trading.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

from ag.readiness.decision_engine import (
    CheckStatus,
    ReadinessGate,
    ReadinessReport,
    ReadinessState,
    ValidatorResult,
)
from ag.readiness.validators import (
    backtest_validator,
    edge_validator,
    infra_validator,
    replay_validator,
    risk_validator,
    system_health_validator,
)

__all__ = [
    "CheckStatus", "ReadinessGate", "ReadinessReport", "ReadinessState",
    "ValidatorResult", "backtest_validator", "edge_validator", "infra_validator",
    "replay_validator", "risk_validator", "system_health_validator",
    "evaluate_readiness",
]


def evaluate_readiness(
    *,
    detect_fns: Optional[Sequence[tuple[str, Callable]]] = None,
    df=None,
    gate_result=None,
    alpha_trades_r: Optional[Sequence[float]] = None,
    baseline_trades_r: Optional[Sequence[float]] = None,
    manual_override: bool = False,
) -> ReadinessReport:
    """Run every validator that has inputs and aggregate into one report.

    Missing inputs yield NOT_RUN / NOT_AVAILABLE (fail-closed), so a sparse call
    cannot accidentally read as ready.
    """
    results = [
        backtest_validator(gate_result),
        replay_validator(detect_fns, df) if detect_fns is not None and df is not None
        else ValidatorResult("replay", CheckStatus.NOT_RUN, "no detectors/data supplied"),
        risk_validator(),
        edge_validator(alpha_trades_r, baseline_trades_r),
        system_health_validator(),
        infra_validator(),
    ]
    return ReadinessGate().evaluate(results, manual_override=manual_override)
