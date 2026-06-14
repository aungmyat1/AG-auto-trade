"""Unit tests for CostModel."""
import pytest
from ag.validation.cost_model import CostModel


class TestCostApplication:
    def test_applies_total_cost_to_each_trade(self):
        cm = CostModel(spread_r=0.05, commission_r=0.05, slippage_r=0.05)
        assert cm.total_r == pytest.approx(0.15)
        result = cm.apply([2.0, -1.0])
        assert result[0] == pytest.approx(1.85)
        assert result[1] == pytest.approx(-1.15)

    def test_zero_cost(self):
        cm = CostModel(0, 0, 0)
        assert cm.apply([1.0, -1.0]) == pytest.approx([1.0, -1.0])

    def test_pf_net_worse_than_gross(self):
        cm = CostModel(0.05, 0.05, 0.05)
        trades = [2.0] * 10 + [-1.0] * 10
        pf_gross = sum(t for t in trades if t > 0) / abs(sum(t for t in trades if t < 0))
        pf_net = cm.profit_factor_net(trades)
        assert pf_net < pf_gross

    def test_factory_gc(self):
        cm = CostModel.for_gc()
        assert cm.total_r == pytest.approx(0.18)

    def test_factory_mgc(self):
        cm = CostModel.for_mgc()
        assert cm.total_r == pytest.approx(0.23)

    def test_mgc_costlier_than_gc(self):
        # Micro commission is not 1/10 → higher relative drag than GC.
        assert CostModel.for_mgc().total_r > CostModel.for_gc().total_r
        # spread/slippage identical (same underlying); only commission differs.
        assert CostModel.for_mgc().spread_r == CostModel.for_gc().spread_r
        assert CostModel.for_mgc().commission_r > CostModel.for_gc().commission_r

    def test_factory_6e(self):
        cm = CostModel.for_6e()
        assert cm.total_r == pytest.approx(0.12)
