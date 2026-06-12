"""
Monte Carlo validation — trade-sequence shuffling.

Shuffles the trade-return sequence N times and measures 5th-percentile PF.
A strategy that passes MC has an edge that isn't purely order-dependent.

Gate: mc_p5_pf(trades_r) > 0.9
"""
from __future__ import annotations

import numpy as np


def _pf(returns: np.ndarray) -> float:
    wins = float(returns[returns > 0].sum())
    losses = float(abs(returns[returns < 0].sum()))
    if losses == 0:
        return float("inf") if wins > 0 else 1.0
    return wins / losses


def run_monte_carlo(
    trades_r: list[float],
    n_iter: int = 10_000,
    seed: int = 42,
) -> float:
    """
    Returns the 5th-percentile PF across n_iter random shuffles.

    Gate threshold: > 0.9
    """
    r = np.array(trades_r, dtype=float)
    rng = np.random.default_rng(seed)

    pfs = np.empty(n_iter)
    for i in range(n_iter):
        shuffled = rng.permutation(r)
        pfs[i] = _pf(shuffled)

    return float(np.percentile(pfs, 5))
