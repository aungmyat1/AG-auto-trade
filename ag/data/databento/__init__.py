"""Databento data layer for CME futures (Phase B).

Offline-first: cached parquet files are served without an API key.
Downloads require DATABENTO_API_KEY in the environment.
"""
from ag.data.databento.loader import (
    DatabentoLoader,
    DatabentoKeyMissingError,
    DatabentoPackageMissingError,
    UnsupportedSymbolError,
    UnsupportedTimeframeError,
    SUPPORTED_SYMBOLS,
)
from ag.data.databento.integrity import (
    check_ohlcv,
    IntegrityReport,
    IntegrityError,
)

__all__ = [
    "DatabentoLoader",
    "DatabentoKeyMissingError",
    "DatabentoPackageMissingError",
    "UnsupportedSymbolError",
    "UnsupportedTimeframeError",
    "SUPPORTED_SYMBOLS",
    "check_ohlcv",
    "IntegrityReport",
    "IntegrityError",
]
