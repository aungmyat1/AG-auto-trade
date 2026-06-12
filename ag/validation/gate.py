"""
Validation Gate — single entry point for the AG robustness battery.

Two-tier verdict (thresholds from AG_AUTO_TRADE_PLAN_v3, FIXED):

  ROBUST : all 9 checks pass → cleared for paper trading / capital
  READ   : floor checks pass (n >= 50, gross PF > 1) → data exists, edge not proven
  FRAGILE: floor checks fail → insufficient evidence; archive and move on

The gate is INTENTIONALLY FIXED. Do not tune thresholds per-instrument.
The confirmation stack's extra degrees of freedom are accounted for via
n_trials in the Deflated Sharpe — every counted knob raises the bar.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Literal

from ag.validation.metrics import BacktestResult
from ag.validation.cost_model import CostModel
from ag.validation.cpcv import run_cpcv
from ag.validation.walk_forward import run_walk_forward
from ag.validation.monte_carlo import run_monte_carlo
from ag.validation.deflated_sharpe import deflated_sharpe_z


@dataclass
class CheckResult:
    name: str
    passed: bool
    value: float
    threshold: float
    op: str = ">"         # '>' | '>=' | '<'
    note: str = ""

    def __str__(self) -> str:
        icon = "PASS" if self.passed else "FAIL"
        op_str = f"{self.op} {self.threshold:.4g}"
        note_str = f" — {self.note}" if self.note else ""
        return f"[{icon}] {self.name}: {self.value:.4g} ({op_str}){note_str}"


@dataclass
class GateResult:
    verdict: Literal["ROBUST", "READ", "FRAGILE"]
    n_trades: int
    checks: list[CheckResult] = field(default_factory=list)

    def report(self) -> str:
        lines = [
            f"VERDICT: {self.verdict}  (n={self.n_trades})",
            "-" * 60,
        ]
        for c in self.checks:
            lines.append(f"  {c}")
        return "\n".join(lines)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_checks(self) -> list[str]:
        return [c.name for c in self.checks if not c.passed]


class ValidationGate:
    """
    Fixed robustness battery (AG_AUTO_TRADE_PLAN_v3).

    Usage:
        gate = ValidationGate()
        result = gate.run(backtest_result, cost_model, n_trials=15)
        print(result.report())
        assert result.verdict in ("ROBUST", "READ")
    """

    # READ floor (minimum to say "data exists")
    READ_N: int = 50
    READ_PF_GROSS: float = 1.0

    # ROBUST thresholds (all must pass)
    ROBUST_N: int = 200
    ROBUST_PF_NET: float = 1.25
    ROBUST_WIN_RATE: float = 0.45
    ROBUST_SHARPE: float = 1.2
    ROBUST_MAX_DD: float = 0.15          # 15%
    ROBUST_CPCV_MEDIAN_PF: float = 1.0
    ROBUST_WF_PASS_PCT: float = 0.60     # 60% of folds PF > 1
    ROBUST_MC_P5_PF: float = 0.9
    ROBUST_DSR_Z: float = 0.0            # z-score > 0

    def run(
        self,
        result: BacktestResult,
        cost_model: CostModel,
        n_trials: int,
    ) -> GateResult:
        """
        Run the full battery.

        Args:
            result     : BacktestResult with trades_r (R-multiples, chronological)
            cost_model : CostModel describing spread/commission/slippage
            n_trials   : number of independent parameter/threshold combos tried
                         for this hypothesis. Count every distinct knob you tuned.
        """
        trades_gross = result.trades_r
        trades_net = cost_model.apply(trades_gross)
        n = len(trades_gross)

        checks: list[CheckResult] = []

        # ── Floor (READ tier) ────────────────────────────────────────────
        pf_gross = _profit_factor(trades_gross)
        checks += [
            CheckResult("n >= 50", n >= self.READ_N, float(n), self.READ_N, ">="),
            CheckResult("gross PF > 1.0", pf_gross > self.READ_PF_GROSS, pf_gross, self.READ_PF_GROSS),
        ]

        if not all(c.passed for c in checks):
            return GateResult("FRAGILE", n, checks)

        # ── ROBUST tier ──────────────────────────────────────────────────
        pf_net = _profit_factor(trades_net)
        win_rate = sum(1 for t in trades_gross if t > 0) / n
        sharpe = _annualized_sharpe(trades_gross)
        max_dd = _max_drawdown(trades_gross)

        checks += [
            CheckResult("n >= 200", n >= self.ROBUST_N, float(n), self.ROBUST_N, ">="),
            CheckResult("net PF > 1.25", pf_net > self.ROBUST_PF_NET, pf_net, self.ROBUST_PF_NET,
                        note=f"cost={cost_model.total_r:.2f}R/trade"),
            CheckResult("win rate > 45%", win_rate > self.ROBUST_WIN_RATE, win_rate, self.ROBUST_WIN_RATE),
            CheckResult("Sharpe > 1.2", sharpe > self.ROBUST_SHARPE, sharpe, self.ROBUST_SHARPE),
            CheckResult("max DD < 15%", max_dd < self.ROBUST_MAX_DD, max_dd, self.ROBUST_MAX_DD, "<"),
        ]

        # Robustness battery (on net returns)
        cpcv_median, cpcv_pct = run_cpcv(trades_net)
        wf_pass_pct = run_walk_forward(trades_net)
        mc_p5 = run_monte_carlo(trades_net)
        dsr_z = deflated_sharpe_z(trades_net, n_trials)

        from math import comb
        n_cpcv_folds = comb(5, 2)

        checks += [
            CheckResult(
                "CPCV median PF > 1.0", cpcv_median > self.ROBUST_CPCV_MEDIAN_PF,
                cpcv_median, self.ROBUST_CPCV_MEDIAN_PF,
                note=f"{n_cpcv_folds} folds ({cpcv_pct:.0%} above 1)",
            ),
            CheckResult(
                "WF pass rate >= 60%", wf_pass_pct >= self.ROBUST_WF_PASS_PCT,
                wf_pass_pct, self.ROBUST_WF_PASS_PCT, ">=",
                note="5-fold purged WF",
            ),
            CheckResult(
                "MC 5th-pct PF > 0.9", mc_p5 > self.ROBUST_MC_P5_PF,
                mc_p5, self.ROBUST_MC_P5_PF,
                note="10k shuffles, seed 42",
            ),
            CheckResult(
                f"DSR z-score > 0 (n_trials={n_trials})", dsr_z > self.ROBUST_DSR_Z,
                dsr_z, self.ROBUST_DSR_Z,
                note="SR deflated for multiple testing",
            ),
        ]

        robust_pass = all(c.passed for c in checks[2:])  # exclude floor
        verdict: Literal["ROBUST", "READ", "FRAGILE"] = "ROBUST" if robust_pass else "READ"
        return GateResult(verdict, n, checks)


# ── Private helpers ──────────────────────────────────────────────────────────

def _profit_factor(trades_r: list[float]) -> float:
    wins = sum(t for t in trades_r if t > 0)
    losses = abs(sum(t for t in trades_r if t < 0))
    if losses == 0:
        return float("inf") if wins > 0 else 1.0
    return wins / losses


def _annualized_sharpe(trades_r: list[float], trades_per_year: int = 252) -> float:
    if len(trades_r) < 2:
        return 0.0
    mu = statistics.mean(trades_r)
    sigma = statistics.stdev(trades_r)
    if sigma == 0:
        return 0.0
    return (mu / sigma) * math.sqrt(trades_per_year)


def _max_drawdown(trades_r: list[float], risk_per_trade: float = 0.005) -> float:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in trades_r:
        equity = equity * (1.0 + r * risk_per_trade)
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd
