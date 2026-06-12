"""
Deflated Sharpe Ratio — Bailey & Lopez de Prado (2014).

Adjusts the observed SR for multiple-testing inflation by estimating
the expected maximum SR from N independent strategy trials.

Gate: deflated_sharpe_z(trades_r, n_trials) > 0

n_trials = total count of parameters + thresholds tried for this hypothesis.
Every distinct threshold combination counts as +1 trial (do not under-count).
The more knobs you tuned, the higher the bar you must clear.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats

# Euler–Mascheroni constant
_GAMMA = 0.5772156649015328


def expected_max_sr(n_trials: int) -> float:
    """
    E[max SR] from N independent strategies of the same backtest length.

    Bailey & Lopez de Prado (2014) eq. 3:
        SR* = (1 - γ)·Φ⁻¹(1 - 1/N) + γ·Φ⁻¹(1 - 1/(N·e))

    Returns 0.0 for N <= 1 (no inflation from single trial).
    """
    if n_trials <= 1:
        return 0.0
    g = _GAMMA
    return (
        (1 - g) * float(stats.norm.ppf(1 - 1 / n_trials))
        + g * float(stats.norm.ppf(1 - 1 / (n_trials * math.e)))
    )


def deflated_sharpe_z(returns: list[float], n_trials: int) -> float:
    """
    DSR z-score. Gate passes when z > 0.

    Positive z means the observed per-trade SR beats the expected maximum
    from n_trials independent random strategies (adjusted for non-normality).

    Args:
        returns   : per-trade R-multiples (net of cost)
        n_trials  : number of independent parameter/threshold combinations
                    tested for this hypothesis (every counted knob = +1)
    """
    r = np.array(returns, dtype=float)
    T = len(r)
    if T < 4:
        return 0.0

    sigma = float(r.std(ddof=1))
    if sigma < 1e-10:
        return 0.0

    sr = float(r.mean()) / sigma  # per-observation SR

    # Non-normality correction terms (Bailey & LP 2014 eq. 4)
    # scipy kurtosis() returns EXCESS kurtosis; raw kurtosis = excess + 3
    skew = float(stats.skew(r))
    raw_kurt = float(stats.kurtosis(r, fisher=True)) + 3.0  # raw (Pearson) kurtosis

    # Variance factor: σ²(SR) ≈ (1/T)(1 - γ₃·SR + (γ₄-1)/4 · SR²)
    variance_factor = 1.0 - skew * sr + ((raw_kurt - 1.0) / 4.0) * sr ** 2
    variance_factor = max(variance_factor, 1e-10)

    sr_star = expected_max_sr(n_trials)
    z = (sr - sr_star) * math.sqrt(T - 1) / math.sqrt(variance_factor)
    return float(z)
