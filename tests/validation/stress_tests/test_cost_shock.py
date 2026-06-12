"""Cost shock stress tests.

Verify that with_shock() correctly scales costs and that shocked costs
degrade net profit factor as expected.
"""
from __future__ import annotations

import random
import pytest

from ag.validation.cost_model import CostModel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trades(n_wins: int, n_losses: int, rr: float, seed: int = 42) -> list:
    rng = random.Random(seed)
    ts = [rr] * n_wins + [-1.0] * n_losses
    rng.shuffle(ts)
    return ts


def _strong() -> list:
    """130 wins at 2.5R, 70 losses. Gross PF ≈ 4.6."""
    return _trades(130, 70, 2.5)


def _borderline() -> list:
    """110 wins at 1.5R, 90 losses. Net PF with 0.15R ≈ 1.44 (passes).
    Under severe shock the net PF drops below 1.25.
    """
    return _trades(110, 90, 1.5)


# ── with_shock() unit tests ───────────────────────────────────────────────────

class TestWithShock:
    def test_spread_scaled(self):
        cm = CostModel(spread_r=0.10, commission_r=0.05, slippage_r=0.05)
        assert cm.with_shock(spread_mult=2.0).spread_r == pytest.approx(0.20)

    def test_slippage_scaled(self):
        cm = CostModel(spread_r=0.05, commission_r=0.05, slippage_r=0.10)
        assert cm.with_shock(slippage_mult=3.0).slippage_r == pytest.approx(0.30)

    def test_commission_unchanged(self):
        cm = CostModel(spread_r=0.05, commission_r=0.08, slippage_r=0.05)
        assert cm.with_shock(2.0, 2.0).commission_r == pytest.approx(0.08)

    def test_returns_new_instance(self):
        cm = CostModel()
        assert cm.with_shock() is not cm

    def test_default_multipliers(self):
        cm = CostModel(spread_r=0.10, commission_r=0.05, slippage_r=0.10)
        shocked = cm.with_shock()   # spread_mult=1.5, slippage_mult=2.0
        assert shocked.spread_r == pytest.approx(0.15)
        assert shocked.slippage_r == pytest.approx(0.20)

    def test_total_r_higher_after_shock(self):
        cm = CostModel.for_gc()
        assert cm.with_shock(1.5, 2.0).total_r > cm.total_r

    def test_for_gc_spread_scaled(self):
        cm = CostModel.for_gc()
        shocked = cm.with_shock(2.0, 1.0)
        assert shocked.spread_r == pytest.approx(cm.spread_r * 2.0)

    def test_for_6e_slippage_scaled(self):
        cm = CostModel.for_6e()
        shocked = cm.with_shock(1.0, 3.0)
        assert shocked.slippage_r == pytest.approx(cm.slippage_r * 3.0)


# ── Gate impact under cost shock ──────────────────────────────────────────────

class TestShockedCostImpact:
    def test_strong_net_pf_positive_under_normal(self):
        assert CostModel().profit_factor_net(_strong()) > 1.25

    def test_strong_net_pf_still_positive_under_moderate_shock(self):
        cm_shocked = CostModel().with_shock(1.5, 2.0)
        # Strong edge survives moderate shock
        assert cm_shocked.profit_factor_net(_strong()) > 1.0

    def test_borderline_passes_normal_costs(self):
        assert CostModel().profit_factor_net(_borderline()) > 1.25

    def test_borderline_fails_under_severe_shock(self):
        cm_shocked = CostModel().with_shock(3.0, 3.0)
        assert cm_shocked.profit_factor_net(_borderline()) < 1.25

    def test_shock_always_reduces_net_pf(self):
        trades = _borderline()
        cm = CostModel()
        cm_shocked = cm.with_shock(1.5, 2.0)
        assert cm_shocked.profit_factor_net(trades) < cm.profit_factor_net(trades)

    def test_apply_cost_shock_reduces_mean_return(self):
        trades = [1.0] * 100 + [-1.0] * 100
        cm = CostModel.for_gc()
        cm_shocked = cm.with_shock(2.0, 2.0)
        mean_normal = sum(cm.apply(trades)) / len(trades)
        mean_shocked = sum(cm_shocked.apply(trades)) / len(trades)
        assert mean_shocked < mean_normal
