"""Synthetic trade scenarios (R-multiples) for gate stress-testing.

Each function returns list[float] of per-trade R-multiples (chronological).
Seeds are fixed so test outcomes are reproducible.

Expected gate verdicts (with CostModel() default = 0.15R/trade, n_trials=1):
  trend_with_pullbacks     → ROBUST  (strong edge, n=200)
  choppy_ranging           → FRAGILE (gross PF < 1.0)
  liquidity_grab_reversal  → READ    (good edge but n=150 < 200)
  failed_breakout_inducement → FRAGILE (negative expectancy)
  news_spike_reversion     → FRAGILE (n=45 < 50 floor)
"""
from __future__ import annotations

import random
from typing import List


def _shuffle(trades: List[float], seed: int) -> List[float]:
    rng = random.Random(seed)
    result = trades[:]
    rng.shuffle(result)
    return result


def trend_with_pullbacks(
    n: int = 200,
    win_rate: float = 0.65,
    rr: float = 2.5,
    seed: int = 42,
) -> List[float]:
    """Strong trend with pullbacks: high win rate and RR.

    Gross PF ≈ 4.6.  Expected verdict: ROBUST.
    """
    n_wins = round(n * win_rate)
    trades = [rr] * n_wins + [-1.0] * (n - n_wins)
    return _shuffle(trades, seed)


def choppy_ranging(
    n: int = 200,
    win_rate: float = 0.52,
    rr: float = 0.90,
    seed: int = 42,
) -> List[float]:
    """Choppy ranging market: marginal win-rate with poor RR.

    Gross PF = 0.52*0.90 / 0.48 ≈ 0.975 < 1.0.  Expected verdict: FRAGILE.
    """
    n_wins = round(n * win_rate)
    trades = [rr] * n_wins + [-1.0] * (n - n_wins)
    return _shuffle(trades, seed)


def liquidity_grab_reversal(
    n: int = 150,
    win_rate: float = 0.60,
    rr: float = 2.0,
    seed: int = 42,
) -> List[float]:
    """Liquidity grab + reversal: real edge but low trade count.

    Gross PF = 3.0.  Expected verdict: READ  (n=150 < 200 ROBUST floor).
    """
    n_wins = round(n * win_rate)
    trades = [rr] * n_wins + [-1.0] * (n - n_wins)
    return _shuffle(trades, seed)


def failed_breakout_inducement(
    n: int = 120,
    win_rate: float = 0.38,
    rr: float = 0.90,
    seed: int = 42,
) -> List[float]:
    """Inducement trap: low win rate and poor RR — negative expectancy.

    Gross PF = 0.38*0.90 / 0.62 ≈ 0.55 < 1.0.  Expected verdict: FRAGILE.
    """
    n_wins = round(n * win_rate)
    trades = [rr] * n_wins + [-1.0] * (n - n_wins)
    return _shuffle(trades, seed)


def news_spike_reversion(
    n: int = 45,
    win_rate: float = 0.62,
    rr: float = 3.0,
    seed: int = 42,
) -> List[float]:
    """High-RR trades from news spikes: good edge but too few trades.

    n=45 < 50 READ floor.  Expected verdict: FRAGILE.
    """
    n_wins = round(n * win_rate)
    trades = [rr] * n_wins + [-1.0] * (n - n_wins)
    return _shuffle(trades, seed)
