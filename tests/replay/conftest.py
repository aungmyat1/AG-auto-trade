"""Fixtures for the replay / look-ahead verification suite."""
from __future__ import annotations

import pandas as pd
import pytest

from ._smc_cases import make_structured_ohlcv


@pytest.fixture(scope="session")
def structured_df() -> pd.DataFrame:
    return make_structured_ohlcv()
