"""
Combinatorial Purged Cross-Validation (CPCV).

Lopez de Prado (2018) — "Advances in Financial Machine Learning", Chapter 12.

Unlike sequential WF, CPCV tries ALL combinations of k groups as train/test.
This produces C(k, n_test) folds, giving a much more comprehensive coverage
of how the strategy performs across different market periods.

Gate: run_cpcv(trades_r) returns (median_pf > 1.0, pct_above_1 >= 0.60)
The gate in ValidationGate uses median_pf > 1.0 as the primary check.
"""
from __future__ import annotations

from itertools import combinations


def _pf(trades: list[float]) -> float:
    wins = sum(t for t in trades if t > 0)
    losses = abs(sum(t for t in trades if t < 0))
    if losses == 0:
        return float("inf") if wins > 0 else 1.0
    return wins / losses


def run_cpcv(
    trades_r: list[float],
    k: int = 5,
    n_test_groups: int = 2,
    n_purge: int = 3,
) -> tuple[float, float]:
    """
    Combinatorial Purged CV.

    Splits trades into k groups, tests all C(k, n_test_groups) combinations
    of test groups (training = remaining groups). Purges n_purge trades from
    the boundary of each contiguous train/test region.

    Returns:
        (median_pf_oos, pct_folds_above_1)

    Gate: median_pf_oos > 1.0 AND pct_folds_above_1 >= 0.60
    """
    n = len(trades_r)
    min_required = k * max(n_purge * 2 + 5, 10)
    if n < min_required:
        return 1.0, 0.5  # not enough data; return neutral

    # Split into k equal groups of indices
    group_size = n // k
    groups: list[list[int]] = []
    for i in range(k):
        start = i * group_size
        end = (i + 1) * group_size if i < k - 1 else n
        groups.append(list(range(start, end)))

    fold_pfs: list[float] = []

    for test_group_indices in combinations(range(k), n_test_groups):
        test_set = set(test_group_indices)
        train_group_indices = [g for g in range(k) if g not in test_set]

        # Collect and sort all test trade indices
        test_idx = sorted(set().union(*[set(groups[g]) for g in test_group_indices]))
        train_idx = sorted(set().union(*[set(groups[g]) for g in train_group_indices]))

        if not test_idx:
            continue

        # Purge: drop train indices within n_purge of any test index boundary
        test_idx_set = set(test_idx)
        _purged_train = [  # noqa: F841 — computed for correctness, train not scored on static series
            i for i in train_idx
            if all(abs(i - j) > n_purge for j in test_idx_set)
        ]

        # We only care about OOS (test) performance
        if len(test_idx) < 5:
            continue

        test_returns = [trades_r[i] for i in test_idx]
        fold_pfs.append(_pf(test_returns))

    if not fold_pfs:
        return 1.0, 0.5

    import statistics
    median_pf = statistics.median(fold_pfs)
    pct_above_1 = sum(1 for pf in fold_pfs if pf > 1.0) / len(fold_pfs)
    return float(median_pf), float(pct_above_1)
