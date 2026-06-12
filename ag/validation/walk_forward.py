"""
Purged Walk-Forward validation.

Sequential train/test splits — the standard time-series CV baseline.
"Purging" removes the n_purge trades nearest each train/test boundary to
prevent information leakage from autocorrelated positions.

Gate: run_walk_forward(trades_r) >= 0.60  (60% of folds with PF > 1)
"""
from __future__ import annotations


def _pf(trades: list[float]) -> float:
    wins = sum(t for t in trades if t > 0)
    losses = abs(sum(t for t in trades if t < 0))
    if losses == 0:
        return float("inf") if wins > 0 else 1.0
    return wins / losses


def run_walk_forward(
    trades_r: list[float],
    n_splits: int = 5,
    test_fraction: float = 0.20,
    n_purge: int = 3,
) -> float:
    """
    Purged walk-forward cross-validation.

    Splits trades into n_splits sequential folds, each tested on the last
    test_fraction of its window. Purges n_purge trades from each boundary.

    Returns: fraction of folds where OOS PF > 1.0 (gate threshold: 0.60)
    """
    n = len(trades_r)
    if n < n_splits * 10:
        # Insufficient data for a meaningful split
        return 0.5

    fold_size = n // n_splits
    results = []

    for i in range(n_splits):
        end = (i + 1) * fold_size if i < n_splits - 1 else n
        train_end = end - int(fold_size * test_fraction)

        # Purge boundary: n_purge trades dropped at each train/test edge
        _purged_train_end = max(train_end - n_purge, 0)  # noqa: F841 — train not scored on static series
        purged_test_start = min(train_end + n_purge, end)

        test_trades = trades_r[purged_test_start:end]
        if len(test_trades) < 5:
            continue

        results.append(_pf(test_trades))

    if not results:
        return 0.0

    return sum(1 for pf in results if pf > 1.0) / len(results)
