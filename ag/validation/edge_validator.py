"""Strategy Edge Validator.

Tests whether an alpha's trade log shows a statistically meaningful edge
over random-entry and naive-trend baselines.

Strategy-agnostic: operates on R-multiples only, no price data needed.
The "random" baseline = permutation test on the actual trade outcomes (shuffles
win/loss labels, preserving trade count and R-size distribution).

Pre-registered threshold: alpha must outperform random baseline by >= 10%.
Source: ag/validation/lock_before_look/TRGS_THRESHOLDS.md
"""
from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import List


@dataclass
class EdgeResult:
    alpha_pf: float
    random_baseline_pf: float        # median PF across permutations
    random_p_value: float            # P(permuted PF >= actual PF) under null
    outperformance_pct: float        # (alpha_pf - random_baseline_pf) / random_baseline_pf
    edge_threshold_pct: float        # minimum required outperformance
    passed: bool
    n_trades: int
    n_permutations: int
    details: List[str] = field(default_factory=list)

    def report(self) -> str:
        icon = "PASS" if self.passed else "FAIL"
        lines = [
            f"[{icon}] EdgeValidator  (n={self.n_trades}, perms={self.n_permutations})",
            f"  alpha PF:          {self.alpha_pf:.4f}",
            f"  random median PF:  {self.random_baseline_pf:.4f}",
            f"  outperformance:    {self.outperformance_pct:+.1%}  (required >= {self.edge_threshold_pct:.0%})",
            f"  p-value (1-tail):  {self.random_p_value:.4f}  (p < 0.05 = signal above noise)",
        ]
        for d in self.details:
            lines.append(f"  note: {d}")
        return "\n".join(lines)


class EdgeValidator:
    """Compare alpha trade log against random-entry and naive-trend baselines.

    Uses a permutation test: win/loss labels on the actual R-multiples are
    randomly shuffled N times.  The null distribution of PF under 'no edge'
    is measured empirically rather than assumed normal.

    Pre-registered outperformance threshold: 10% (TRGS_THRESHOLDS.md).
    """

    OUTPERFORMANCE_THRESHOLD: float = 0.10    # 10% above random baseline PF
    DEFAULT_N_PERMUTATIONS: int = 10_000
    SEED: int = 42

    def validate(
        self,
        trades_r: List[float],
        n_permutations: int = DEFAULT_N_PERMUTATIONS,
    ) -> EdgeResult:
        """Validate edge of an alpha's trade log against the random baseline.

        Args:
            trades_r: List of R-multiples (positive = win, negative = loss).
                      Must contain >= 50 trades.
            n_permutations: Number of random permutations for the null distribution.

        Returns:
            EdgeResult with pass/fail and all supporting statistics.
        """
        n = len(trades_r)
        details: List[str] = []

        if n < 50:
            details.append(f"insufficient trades (n={n}, min=50) — edge cannot be estimated")
            return EdgeResult(
                alpha_pf=_profit_factor(trades_r),
                random_baseline_pf=1.0,
                random_p_value=1.0,
                outperformance_pct=-1.0,
                edge_threshold_pct=self.OUTPERFORMANCE_THRESHOLD,
                passed=False,
                n_trades=n,
                n_permutations=n_permutations,
                details=details,
            )

        alpha_pf = _profit_factor(trades_r)

        # Permutation null distribution: shuffle which R-multiples are assigned
        # to each position.  This preserves trade count and R-size distribution
        # but destroys any time-based edge.
        rng = random.Random(self.SEED)
        shuffled_pfs: List[float] = []
        mags = [abs(r) for r in trades_r]
        for _ in range(n_permutations):
            signs = [1 if rng.random() >= 0.5 else -1 for _ in range(n)]
            shuffled = [m * s for m, s in zip(mags, signs)]
            shuffled_pfs.append(_profit_factor(shuffled))

        shuffled_pfs.sort()
        random_median_pf = statistics.median(shuffled_pfs)

        # p-value: proportion of permutations that matched or exceeded the alpha PF
        n_above = sum(1 for pf in shuffled_pfs if pf >= alpha_pf)
        p_value = n_above / n_permutations

        if random_median_pf <= 0:
            outperformance = float("inf")
        else:
            outperformance = (alpha_pf - random_median_pf) / random_median_pf

        passed = outperformance >= self.OUTPERFORMANCE_THRESHOLD

        if p_value < 0.05:
            details.append("p < 0.05: alpha PF is unlikely under the null (good)")
        else:
            details.append(f"p = {p_value:.3f}: alpha PF is within the random distribution")

        # Naive trend baseline: consecutive-same-direction filter (keep only
        # trades where the previous trade was a winner — momentum filter).
        # This proxy estimates whether even a simple trend rule beats random.
        trend_trades = [trades_r[i] for i in range(1, n) if trades_r[i - 1] > 0]
        if len(trend_trades) >= 10:
            trend_pf = _profit_factor(trend_trades)
            details.append(f"naive trend baseline PF: {trend_pf:.4f} (n={len(trend_trades)})")
            if alpha_pf > trend_pf:
                details.append("alpha PF > naive trend baseline: GOOD")
            else:
                details.append("alpha PF <= naive trend baseline: WARN — check if alpha adds value over naive trend")

        return EdgeResult(
            alpha_pf=alpha_pf,
            random_baseline_pf=random_median_pf,
            random_p_value=p_value,
            outperformance_pct=outperformance,
            edge_threshold_pct=self.OUTPERFORMANCE_THRESHOLD,
            passed=passed,
            n_trades=n,
            n_permutations=n_permutations,
            details=details,
        )


def _profit_factor(trades_r: List[float]) -> float:
    wins = sum(r for r in trades_r if r > 0)
    losses = abs(sum(r for r in trades_r if r < 0))
    if losses == 0:
        return float("inf") if wins > 0 else 1.0
    return wins / losses
