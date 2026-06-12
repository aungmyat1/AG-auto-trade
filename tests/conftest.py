"""Shared pytest fixtures for ag-auto-trade tests."""
import pytest
from ag.validation.cost_model import CostModel


@pytest.fixture
def strong_trades():
    """300 trades: 60% win, 2:1 RR — should pass ROBUST gate."""
    import random
    random.seed(42)
    return [2.0 if random.random() < 0.60 else -1.0 for _ in range(300)]


@pytest.fixture
def marginal_trades():
    """100 trades: 51% win, 1.1:1 RR — should READ at best."""
    import random
    random.seed(42)
    return [1.1 if random.random() < 0.51 else -1.0 for _ in range(100)]


@pytest.fixture
def default_cost():
    return CostModel()


@pytest.fixture
def zero_cost():
    return CostModel(0, 0, 0)
