"""IB data integrity — thin delegation to the shared OHLCV checker.

The shared check_ohlcv() in ag.data.databento.integrity validates the same
five-column schema that IBHistoricalLoader produces. No duplication needed.
"""
from __future__ import annotations

# Re-export so callers can write:
#   from ag.data.ib_live.integrity import check_ohlcv, IntegrityReport, IntegrityError
from ag.data.databento.integrity import (  # noqa: F401
    check_ohlcv,
    IntegrityReport,
    IntegrityError,
)
