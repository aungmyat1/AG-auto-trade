"""Databento OHLCV loader for CME futures — offline-first, parquet-cached.

Design:
  Cache hit   → returns parquet immediately, no API key needed, no network.
  Cache miss  → downloads from Databento, writes parquet, then returns.
                Requires DATABENTO_API_KEY and the `databento` package.

Supported instruments:  GC (Gold), MGC (Micro Gold), 6E (Euro FX)
Supported timeframes:   "1m" (1-minute), "1h" (1-hour)
Dataset:                GLBX.MDP3 (CME Globex)
Continuous contract:    <SYM>.c.0  (nearest front-month, back-adjusted by Databento)

Usage (offline from cache):
    loader = DatabentoLoader()
    df = loader.load("GC", "1h")            # loads data/cache/GC_1h.parquet

Usage (first download):
    # DATABENTO_API_KEY must be set in .env / environment
    loader = DatabentoLoader()
    df = loader.load("GC", "1h", start="2022-01-01", end="2024-12-31")
    # Writes data/cache/GC_1h.parquet for future offline use

DataFrame columns returned:
    timestamp (DatetimeTZDtype UTC, index), open, high, low, close, volume (float64)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

DATASET = "GLBX.MDP3"

SUPPORTED_SYMBOLS = {"GC", "MGC", "6E"}

# Databento continuous-contract symbol format
_DB_SYMBOL = {
    "GC":  "GC.c.0",
    "MGC": "MGC.c.0",
    "6E":  "6E.c.0",
}

_DB_SCHEMA = {
    "1m": "ohlcv-1m",
    "1h": "ohlcv-1h",
}

# Default cache directory (repo-relative; override via DatabentoLoader(cache_dir=...))
_DEFAULT_CACHE_DIR = Path(__file__).parents[4] / "data" / "cache"


# ── Exceptions ────────────────────────────────────────────────────────────────

class DatabentoKeyMissingError(RuntimeError):
    """DATABENTO_API_KEY is not set — required for downloads (not for cache reads)."""


class DatabentoPackageMissingError(ImportError):
    """The `databento` package is not installed — required for downloads."""


class UnsupportedSymbolError(ValueError):
    pass


class UnsupportedTimeframeError(ValueError):
    pass


# ── Loader ────────────────────────────────────────────────────────────────────

class DatabentoLoader:
    """Offline-first OHLCV loader. Uses parquet cache; downloads only on miss."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR

    # ── Public API ────────────────────────────────────────────────────────────

    def load(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return OHLCV DataFrame for symbol+timeframe.

        Args:
            symbol:    "GC" | "MGC" | "6E"
            timeframe: "1m" | "1h"
            start:     ISO date string, e.g. "2022-01-01" — required on cache miss
            end:       ISO date string, e.g. "2024-12-31" — required on cache miss

        Returns:
            DataFrame with UTC DatetimeIndex and columns [open, high, low, close, volume].

        Raises:
            UnsupportedSymbolError    if symbol not in SUPPORTED_SYMBOLS
            UnsupportedTimeframeError if timeframe not in {"1m", "1h"}
            DatabentoKeyMissingError  if cache miss and API key not set
            DatabentoPackageMissingError if cache miss and databento not installed
        """
        self._validate(symbol, timeframe)
        cache_path = self._cache_path(symbol, timeframe)

        if cache_path.exists():
            logger.info("Cache hit: %s", cache_path)
            return self._read_cache(cache_path)

        if start is None or end is None:
            raise ValueError(
                f"No cache found at {cache_path}. "
                "Provide start= and end= to trigger a download."
            )

        logger.info("Cache miss — downloading %s %s %s→%s", symbol, timeframe, start, end)
        df = self._download(symbol, timeframe, start, end)
        self._write_cache(df, cache_path)
        return df

    def cache_exists(self, symbol: str, timeframe: str) -> bool:
        """True if the parquet cache file already exists."""
        self._validate(symbol, timeframe)
        return self._cache_path(symbol, timeframe).exists()

    def cache_path(self, symbol: str, timeframe: str) -> Path:
        """Return the cache file path (may or may not exist)."""
        self._validate(symbol, timeframe)
        return self._cache_path(symbol, timeframe)

    # ── Download ──────────────────────────────────────────────────────────────

    def _download(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        api_key = os.environ.get("DATABENTO_API_KEY", "")
        if not api_key:
            raise DatabentoKeyMissingError(
                "DATABENTO_API_KEY is not set. "
                "Add it to .env or export it before downloading. "
                "Once the cache exists, the key is no longer needed."
            )

        try:
            import databento as db  # type: ignore[import]
        except ImportError as exc:
            raise DatabentoPackageMissingError(
                "The `databento` package is not installed. "
                "Run: pip install databento"
            ) from exc

        client = db.Historical(api_key)
        data = client.timeseries.get_range(
            dataset=DATASET,
            symbols=[_DB_SYMBOL[symbol]],
            schema=_DB_SCHEMA[timeframe],
            start=start,
            end=end,
        )
        df = data.to_df()
        return self._normalise(df, symbol)

    # ── Cache I/O ─────────────────────────────────────────────────────────────

    def _cache_path(self, symbol: str, timeframe: str) -> Path:
        return self.cache_dir / f"{symbol}_{timeframe}.parquet"

    def _read_cache(self, path: Path) -> pd.DataFrame:
        df = pd.read_parquet(path)
        self._ensure_utc_index(df)
        return df

    def _write_cache(self, df: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=True)
        logger.info("Cached → %s  (%d bars)", path, len(df))

    # ── Normalisation ─────────────────────────────────────────────────────────

    def _normalise(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Standardise Databento output to [open, high, low, close, volume]."""
        col_map = {}
        for col in df.columns:
            lower = col.lower()
            for target in ("open", "high", "low", "close", "volume"):
                if target in lower:
                    col_map[col] = target
                    break

        df = df.rename(columns=col_map)
        keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
        df = df[keep].copy()

        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = df[col].astype("float64")

        self._ensure_utc_index(df)
        df.sort_index(inplace=True)
        df.attrs["symbol"] = symbol
        return df

    @staticmethod
    def _ensure_utc_index(df: pd.DataFrame) -> None:
        if not isinstance(df.index, pd.DatetimeIndex):
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)
            elif "ts_event" in df.columns:
                df.set_index("ts_event", inplace=True)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        elif str(df.index.tz) != "UTC":
            df.index = df.index.tz_convert("UTC")

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def _validate(symbol: str, timeframe: str) -> None:
        if symbol not in SUPPORTED_SYMBOLS:
            raise UnsupportedSymbolError(
                f"Symbol '{symbol}' not supported. Valid: {sorted(SUPPORTED_SYMBOLS)}"
            )
        if timeframe not in _DB_SCHEMA:
            raise UnsupportedTimeframeError(
                f"Timeframe '{timeframe}' not supported. Valid: {sorted(_DB_SCHEMA)}"
            )
