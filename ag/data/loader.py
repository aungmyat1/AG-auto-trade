"""Source-agnostic OHLCV loader factory.

Both loaders expose an identical .load(symbol, timeframe, start=, end=) API.
Switch data sources by changing the source= flag — alpha code never changes.

    from ag.data.loader import get_loader

    loader = get_loader("ib")          # Interactive Brokers (Phase B MVP)
    loader = get_loader("databento")   # Databento (deeper history, future upgrade)

    df = loader.load("GC", "1h")           # cache hit — no connection needed
    df = loader.load("GC", "1h",           # cache miss — triggers download
                     start="2024-01-01", end="2024-12-31")
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from ag.data.ib_live.historical import IBHistoricalLoader
from ag.data.ib_live.config import IBConfig
from ag.data.databento.loader import DatabentoLoader

_Loader = Union[IBHistoricalLoader, DatabentoLoader]

_VALID_SOURCES = {"ib", "databento"}


def get_loader(source: str = "ib", cache_dir: Path | None = None) -> _Loader:
    """Return a loader for the given data source.

    Args:
        source:    "ib" (default) | "databento"
        cache_dir: optional path override for the parquet cache

    Returns:
        IBHistoricalLoader or DatabentoLoader — both expose .load() / .cache_exists()
    """
    if source not in _VALID_SOURCES:
        raise ValueError(
            f"Unknown source {source!r}. Valid: {sorted(_VALID_SOURCES)}"
        )
    if source == "ib":
        config = IBConfig(cache_dir=cache_dir) if cache_dir else IBConfig()
        return IBHistoricalLoader(config=config)
    # databento
    return DatabentoLoader(cache_dir=cache_dir)
