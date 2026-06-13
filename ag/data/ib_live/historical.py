"""Interactive Brokers historical OHLCV loader — offline-first, parquet-cached.

Design mirrors DatabentoLoader so the two are interchangeable:

    loader = IBHistoricalLoader()
    df = loader.load("GC", "1h")          # reads parquet cache, no TWS needed
    df = loader.load("GC", "1m",          # downloads from IB, writes cache
                     start="2024-01-01", end="2024-12-31")

Cache hit  → returns parquet immediately, no TWS / IB account needed.
Cache miss → connects to TWS/Gateway (must be running), downloads in chunks
              with 10-second pacing, writes parquet, disconnects.

Continuous contract: uses IB secType='CONTFUT', which returns the back-adjusted
nearest front-month series. No manual roll calculation required.

IB bar schema returned:
    date (DatetimeTZDtype UTC, index), open, high, low, close, volume (float64)
    IB also returns 'average' and 'barCount'; these are dropped.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from ag.data.ib_live.config import (
    IBConfig,
    SUPPORTED_SYMBOLS,
    SUPPORTED_TIMEFRAMES,
    _EXCHANGE,
    _BAR_SIZE,
    _CHUNK_DURATION,
)

logger = logging.getLogger(__name__)


# ── Exceptions ────────────────────────────────────────────────────────────────

class IBConnectionError(RuntimeError):
    """TWS or IB Gateway is not running / reachable on cache miss."""


class IBPackageMissingError(ImportError):
    """The `ib_insync` package is not installed."""


class UnsupportedSymbolError(ValueError):
    pass


class UnsupportedTimeframeError(ValueError):
    pass


# ── Loader ────────────────────────────────────────────────────────────────────

class IBHistoricalLoader:
    """Offline-first IB OHLCV loader. Same interface as DatabentoLoader."""

    def __init__(self, config: Optional[IBConfig] = None) -> None:
        self.config = config or IBConfig()
        self.cache_dir = self.config.cache_dir

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
            start:     ISO date "YYYY-MM-DD" — required on cache miss
            end:       ISO date "YYYY-MM-DD" — required on cache miss (defaults to today)

        Returns:
            DataFrame with UTC DatetimeIndex and columns [open, high, low, close, volume].

        Raises:
            UnsupportedSymbolError    if symbol not in SUPPORTED_SYMBOLS
            UnsupportedTimeframeError if timeframe not in {"1m", "1h"}
            IBConnectionError         if cache miss and TWS/Gateway is not reachable
            IBPackageMissingError     if cache miss and ib_insync not installed
        """
        self._validate(symbol, timeframe)
        path = self._cache_path(symbol, timeframe)

        if path.exists():
            logger.info("Cache hit: %s", path)
            return self._read_cache(path)

        if start is None:
            raise ValueError(
                f"No cache found at {path}. "
                "Provide start= (and optionally end=) to trigger a download."
            )

        end_dt = end or datetime.now(timezone.utc).strftime("%Y%m%d %H:%M:%S")
        logger.info("Cache miss — downloading %s %s %s→%s", symbol, timeframe, start, end_dt)
        df = self._download(symbol, timeframe, start, end_dt)
        self._write_cache(df, path)
        return df

    def cache_exists(self, symbol: str, timeframe: str) -> bool:
        self._validate(symbol, timeframe)
        return self._cache_path(symbol, timeframe).exists()

    def cache_path(self, symbol: str, timeframe: str) -> Path:
        self._validate(symbol, timeframe)
        return self._cache_path(symbol, timeframe)

    # ── Download (chunked, paced) ─────────────────────────────────────────────

    def _download(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        try:
            from ib_insync import IB, Contract, util  # type: ignore[import]
        except ImportError as exc:
            raise IBPackageMissingError(
                "The `ib_insync` package is not installed. "
                "Run: pip install ib_insync"
            ) from exc

        ib = IB()
        try:
            ib.connect(
                self.config.host,
                self.config.port,
                clientId=self.config.client_id,
                timeout=10,
            )
        except Exception as exc:
            raise IBConnectionError(
                f"Cannot connect to TWS/Gateway at "
                f"{self.config.host}:{self.config.port} — is it running? "
                f"Error: {exc}"
            ) from exc

        try:
            contract = Contract(
                symbol=symbol,
                secType="CONTFUT",    # back-adjusted continuous front-month
                exchange=_EXCHANGE[symbol],
                currency="USD",
            )
            ib.qualifyContracts(contract)
            chunks = self._fetch_chunks(ib, contract, timeframe, start, end)
        finally:
            ib.disconnect()

        if not chunks:
            raise ValueError(f"IB returned no bars for {symbol} {timeframe} {start}→{end}")

        df = pd.concat(chunks).sort_index()
        df = df[~df.index.duplicated(keep="last")]
        return df

    def _fetch_chunks(
        self,
        ib,
        contract,
        timeframe: str,
        start: str,
        end: str,
    ) -> list[pd.DataFrame]:
        from ib_insync import util  # already imported in caller scope, but guard here

        bar_size = _BAR_SIZE[timeframe]
        chunk_dur = _CHUNK_DURATION[timeframe]

        start_ts = pd.Timestamp(start, tz="UTC")
        end_ts = pd.Timestamp(end if " " in end else end + " 23:59:59", tz="UTC")
        current_end = end_ts
        chunks: list[pd.DataFrame] = []

        while current_end > start_ts:
            end_str = current_end.strftime("%Y%m%d %H:%M:%S")
            logger.info("IB chunk request: end=%s dur=%s bar=%s", end_str, chunk_dur, bar_size)

            bars = ib.reqHistoricalData(
                contract,
                endDateTime=end_str,
                durationStr=chunk_dur,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=False,     # include electronic session
                formatDate=2,     # UTC epoch seconds
            )

            if not bars:
                break

            df_chunk = util.df(bars)
            df_chunk = self._normalise(df_chunk)
            chunks.append(df_chunk)

            oldest = df_chunk.index.min()
            if oldest <= start_ts:
                break

            current_end = oldest - pd.Timedelta(seconds=1)
            logger.info("Pacing sleep %ss before next chunk", self.config.pacing_secs)
            time.sleep(self.config.pacing_secs)

        return chunks

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

    def _normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardise IB bar output to [open, high, low, close, volume]."""
        # IB formatDate=2 gives 'date' column as int64 UTC epoch seconds
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], unit="s", utc=True)
            df = df.set_index("date")

        df.index.name = "timestamp"

        keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
        df = df[keep].copy()

        for col in keep:
            df[col] = df[col].astype("float64")

        self._ensure_utc_index(df)
        return df

    @staticmethod
    def _ensure_utc_index(df: pd.DataFrame) -> None:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be DatetimeIndex after normalisation")
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
        if timeframe not in SUPPORTED_TIMEFRAMES:
            raise UnsupportedTimeframeError(
                f"Timeframe '{timeframe}' not supported. Valid: {sorted(SUPPORTED_TIMEFRAMES)}"
            )
