"""IB historical data layer for CME futures (Phase B — IB path).

Offline-first: cached parquet files are served without a running TWS instance.
Downloads require TWS or IB Gateway running + ib_insync installed.
"""
from ag.data.ib_live.historical import (
    IBHistoricalLoader,
    IBConnectionError,
    IBPackageMissingError,
    UnsupportedSymbolError,
    UnsupportedTimeframeError,
)
from ag.data.ib_live.config import IBConfig, SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES
from ag.data.ib_live.integrity import check_ohlcv, IntegrityReport, IntegrityError

__all__ = [
    "IBHistoricalLoader",
    "IBConfig",
    "IBConnectionError",
    "IBPackageMissingError",
    "UnsupportedSymbolError",
    "UnsupportedTimeframeError",
    "SUPPORTED_SYMBOLS",
    "SUPPORTED_TIMEFRAMES",
    "check_ohlcv",
    "IntegrityReport",
    "IntegrityError",
]
