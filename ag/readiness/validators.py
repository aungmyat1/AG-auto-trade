"""TRGS validators — each composes an existing, locked subsystem and returns a
ValidatorResult. Strategy-agnostic and deterministic; no market assumptions.

  backtest  → wraps the locked ValidationGate verdict (ROBUST required)
  replay    → wraps ag.validation.replay_harness (no look-ahead / no repaint)
  risk      → exercises the locked RiskEngine guards (locked 0.5%/2%/15%/5x/3)
  edge      → compares an alpha's trades to a baseline (must outperform)
  system_health / infra → NOT_AVAILABLE until the Phase-D execution layer exists
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

from ag.readiness.decision_engine import CheckStatus, ValidatorResult
from ag.risk.engine import RiskConfig, RiskEngine
from ag.validation.replay_harness import future_leak_free, repaint_free


# ── backtest ──────────────────────────────────────────────────────────────────

def backtest_validator(gate_result=None) -> ValidatorResult:
    """PASS only on a ROBUST verdict from the locked ValidationGate.

    gate_result is a ValidationGate.run(...) output (has .verdict). None ⇒ NOT_RUN.
    READ / FRAGILE are explicitly not deployable.
    """
    if gate_result is None:
        return ValidatorResult("backtest", CheckStatus.NOT_RUN,
                               "no gate verdict yet (needs real GC data + run_gate)")
    verdict = getattr(gate_result, "verdict", None)
    ev = {"verdict": verdict, "n_trades": getattr(gate_result, "n_trades", None)}
    if verdict == "ROBUST":
        return ValidatorResult("backtest", CheckStatus.PASS, "ROBUST verdict", ev)
    return ValidatorResult("backtest", CheckStatus.FAIL,
                           f"verdict {verdict} is not ROBUST", ev)


# ── replay integrity ──────────────────────────────────────────────────────────

def replay_validator(
    detect_fns: Sequence[tuple[str, Callable]],
    df,
    *,
    splits: Sequence[int] = (120, 180, 240),
) -> ValidatorResult:
    """FAIL if ANY detector leaks the future or repaints. This is the anti-fake-
    profit gate: a backtest from a peeking detector is worthless."""
    if not detect_fns:
        return ValidatorResult("replay", CheckStatus.NOT_RUN, "no detectors supplied")
    leaks, repaints = [], []
    for name, fn in detect_fns:
        if not all(future_leak_free(fn, df, s) for s in splits):
            leaks.append(name)
        if not repaint_free(fn, df, splits):
            repaints.append(name)
    if leaks or repaints:
        return ValidatorResult(
            "replay", CheckStatus.FAIL,
            f"look-ahead={leaks or '-'} repaint={repaints or '-'}",
            {"lookahead": leaks, "repainting": repaints},
        )
    return ValidatorResult("replay", CheckStatus.PASS,
                           f"{len(detect_fns)} detectors: no look-ahead, no repaint")


# ── risk engine ───────────────────────────────────────────────────────────────

def risk_validator(config: Optional[RiskConfig] = None) -> ValidatorResult:
    """Verify each locked guard actually blocks. Uses LOCKED limits, not the
    TRGS-doc's 3%/10% (which would relax the engine)."""
    cfg = config or RiskConfig()
    fired: dict[str, bool] = {}

    # baseline: a clean entry is approved
    fired["baseline_ok"] = RiskEngine(cfg).validate_entry(0.005, leverage=1.0).approved

    # G1 daily loss
    e = RiskEngine(cfg)
    e.daily_pnl_pct = -cfg.max_daily_loss_pct
    fired["G1_daily"] = any("G1" in v for v in e.validate_entry(0.005).violations)

    # G2 drawdown
    e = RiskEngine(cfg)
    e.peak_balance, e.current_balance = 1.0, 1.0 - cfg.max_drawdown_pct
    fired["G2_drawdown"] = any("G2" in v for v in e.validate_entry(0.005).violations)

    # G3 cooldown after consecutive losses
    e = RiskEngine(cfg)
    for _ in range(cfg.max_consecutive_losses):
        e.record_trade_result(-0.001)
    fired["G3_cooldown"] = any("G3" in v for v in e.validate_entry(0.005).violations)

    # G4 position size cap
    e = RiskEngine(cfg)
    fired["G4_size"] = any(
        "G4" in v for v in e.validate_entry(cfg.max_position_size_pct * 2).violations
    )

    # G5 leverage cap
    e = RiskEngine(cfg)
    fired["G5_leverage"] = any(
        "G5" in v for v in e.validate_entry(0.005, leverage=cfg.max_leverage + 1).violations
    )

    ok = fired.get("baseline_ok") and all(
        v for k, v in fired.items() if k != "baseline_ok"
    )
    status = CheckStatus.PASS if ok else CheckStatus.FAIL
    detail = "all guards fire (G1-G5) on locked limits" if ok else f"guard gap: {fired}"
    return ValidatorResult("risk", status, detail, fired)


# ── strategy edge vs baseline ─────────────────────────────────────────────────

def _expectancy(trades_r: Sequence[float]) -> float:
    return sum(trades_r) / len(trades_r) if trades_r else 0.0


def edge_validator(
    alpha_trades_r: Optional[Sequence[float]],
    baseline_trades_r: Optional[Sequence[float]],
    *,
    min_outperformance: float = 0.10,
) -> ValidatorResult:
    """Alpha must beat a baseline (random / trend) expectancy by >= 10% and be
    positive. Prevents false confidence from a marginally-better-than-noise edge."""
    if not alpha_trades_r or not baseline_trades_r:
        return ValidatorResult("edge", CheckStatus.NOT_RUN,
                               "alpha and/or baseline trades not supplied")
    a, b = _expectancy(alpha_trades_r), _expectancy(baseline_trades_r)
    ev = {"alpha_expectancy_r": round(a, 4), "baseline_expectancy_r": round(b, 4),
          "min_outperformance": min_outperformance}
    # require positive expectancy AND a clear margin over baseline
    threshold = b + abs(b) * min_outperformance if b > 0 else b + min_outperformance
    if a > 0 and a >= threshold:
        return ValidatorResult("edge", CheckStatus.PASS,
                               f"alpha {a:.3f}R beats baseline {b:.3f}R", ev)
    return ValidatorResult("edge", CheckStatus.FAIL,
                           f"alpha {a:.3f}R does not beat baseline {b:.3f}R by {min_outperformance:.0%}",
                           ev)


# ── execution-dependent (Phase D — locked) ────────────────────────────────────

def system_health_validator() -> ValidatorResult:
    """API/order/DB/journal/dup-order/kill-switch health. The execution layer is
    not built (Phase D locked until a ROBUST verdict), so this fails closed."""
    return ValidatorResult(
        "system_health", CheckStatus.NOT_AVAILABLE,
        "execution layer not built (Phase D locked) — cannot verify live health",
        {"phase": "D", "locked": True},
    )


def infra_validator() -> ValidatorResult:
    """VPS-restart / API-failure / network-drop / exchange-delay resilience.
    Requires a running execution layer; NOT_AVAILABLE until Phase D."""
    return ValidatorResult(
        "infra", CheckStatus.NOT_AVAILABLE,
        "resilience scenarios require the Phase-D execution layer (locked)",
        {"phase": "D", "locked": True},
    )
