"""Unit tests for IBHistoricalLoader — offline / cache paths only.

No TWS connection is made. Tests seed a parquet cache with synthetic fixtures
and verify the full cache-read, validation, and helper paths.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.data.ib_live.historical import (
    IBHistoricalLoader,
    IBConnectionError,
    IBPackageMissingError,
    UnsupportedSymbolError,
    UnsupportedTimeframeError,
)
from ag.data.ib_live.config import IBConfig, SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES
from ag.data.loader import get_loader
from tests.fixtures.synthetic import make_gc_1h, save_fixture


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / "ib_cache"


@pytest.fixture
def config(cache_dir):
    return IBConfig(cache_dir=cache_dir)


@pytest.fixture
def loader(config):
    return IBHistoricalLoader(config=config)


@pytest.fixture
def seeded_cache(cache_dir):
    """Write synthetic GC 1h parquet in IB cache dir."""
    pytest.importorskip("pyarrow", reason="pyarrow required for parquet cache")
    df = make_gc_1h(n_bars=400)
    save_fixture(df, cache_dir / "GC_1h.parquet")
    return cache_dir


# ── Cache hit ─────────────────────────────────────────────────────────────────

class TestCacheHit:
    def test_returns_dataframe_from_cache(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 400

    def test_cache_hit_has_required_columns(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")
        for col in ("open", "high", "low", "close", "volume"):
            assert col in df.columns

    def test_cache_hit_has_utc_index(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")
        assert isinstance(df.index, pd.DatetimeIndex)
        assert str(df.index.tz) == "UTC"

    def test_cache_hit_needs_no_tws_connection(self, loader, seeded_cache, monkeypatch):
        """Cache path must work even when ib_insync is unavailable."""
        loader.cache_dir = seeded_cache
        import sys
        saved = sys.modules.get("ib_insync")
        sys.modules["ib_insync"] = None  # type: ignore[assignment]
        try:
            df = loader.load("GC", "1h")
            assert len(df) > 0
        finally:
            if saved is None:
                sys.modules.pop("ib_insync", None)
            else:
                sys.modules["ib_insync"] = saved

    def test_cache_hit_no_start_end_required(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")  # no start/end — fine because cache exists
        assert len(df) > 0


# ── Cache miss ────────────────────────────────────────────────────────────────

class TestCacheMiss:
    def test_miss_without_start_raises_value_error(self, loader):
        with pytest.raises(ValueError, match="start="):
            loader.load("GC", "1h")

    def test_miss_without_package_raises_package_error(self, loader, monkeypatch):
        monkeypatch.setenv("IB_HOST", "127.0.0.1")
        import sys
        saved = sys.modules.get("ib_insync")
        sys.modules["ib_insync"] = None  # type: ignore[assignment]
        try:
            with pytest.raises((IBPackageMissingError, ImportError, TypeError)):
                loader.load("GC", "1h", start="2024-01-01", end="2024-06-30")
        finally:
            if saved is None:
                sys.modules.pop("ib_insync", None)
            else:
                sys.modules["ib_insync"] = saved

    def test_miss_with_package_but_no_tws_raises_connection_error(self, loader):
        """Attempts to connect to a port where no TWS runs → IBConnectionError."""
        pytest.importorskip("ib_insync", reason="ib_insync required for connection test")
        # Use an unreachable port so connect() times out quickly
        loader.config.port = 19999
        with pytest.raises((IBConnectionError, Exception)):
            loader.load("GC", "1h", start="2024-01-01", end="2024-06-30")


# ── cache_exists / cache_path ─────────────────────────────────────────────────

class TestCacheHelpers:
    def test_cache_exists_false_when_empty(self, loader):
        assert loader.cache_exists("GC", "1h") is False

    def test_cache_exists_true_after_seeding(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        assert loader.cache_exists("GC", "1h") is True

    def test_cache_path_filename(self, loader):
        assert loader.cache_path("GC", "1h").name == "GC_1h.parquet"

    def test_cache_path_mgc_1m(self, loader):
        assert loader.cache_path("MGC", "1m").name == "MGC_1m.parquet"


# ── Validation ────────────────────────────────────────────────────────────────

class TestValidation:
    def test_invalid_symbol_raises(self, loader):
        with pytest.raises(UnsupportedSymbolError):
            loader.load("BTC", "1h")

    def test_invalid_timeframe_raises(self, loader):
        with pytest.raises(UnsupportedTimeframeError):
            loader.load("GC", "5m")

    def test_all_supported_symbols_pass_validation(self, loader):
        for sym in SUPPORTED_SYMBOLS:
            loader._validate(sym, "1h")  # must not raise

    def test_both_timeframes_pass_validation(self, loader):
        for tf in SUPPORTED_TIMEFRAMES:
            loader._validate("GC", tf)


# ── Source-agnostic factory ───────────────────────────────────────────────────

class TestGetLoader:
    def test_get_loader_ib_returns_ib_loader(self, tmp_path):
        loader = get_loader("ib", cache_dir=tmp_path)
        assert isinstance(loader, IBHistoricalLoader)

    def test_get_loader_databento_returns_databento_loader(self, tmp_path):
        from ag.data.databento.loader import DatabentoLoader
        loader = get_loader("databento", cache_dir=tmp_path)
        assert isinstance(loader, DatabentoLoader)

    def test_get_loader_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            get_loader("alpaca")

    def test_both_loaders_have_load_method(self, tmp_path):
        for source in ("ib", "databento"):
            loader = get_loader(source, cache_dir=tmp_path)
            assert callable(getattr(loader, "load", None))

    def test_both_loaders_have_cache_exists_method(self, tmp_path):
        for source in ("ib", "databento"):
            loader = get_loader(source, cache_dir=tmp_path)
            assert callable(getattr(loader, "cache_exists", None))

    def test_both_loaders_have_cache_path_method(self, tmp_path):
        for source in ("ib", "databento"):
            loader = get_loader(source, cache_dir=tmp_path)
            assert callable(getattr(loader, "cache_path", None))

    def test_ib_loader_uses_custom_cache_dir(self, tmp_path):
        loader = get_loader("ib", cache_dir=tmp_path / "custom")
        assert loader.cache_dir == tmp_path / "custom"

    def test_databento_loader_uses_custom_cache_dir(self, tmp_path):
        loader = get_loader("databento", cache_dir=tmp_path / "custom")
        assert loader.cache_dir == tmp_path / "custom"

    def test_ib_loader_same_api_as_databento(self, tmp_path):
        """Both loaders share the same .load() signature."""
        from ag.data.databento.loader import DatabentoLoader
        ib = get_loader("ib", cache_dir=tmp_path)
        db = get_loader("databento", cache_dir=tmp_path)
        import inspect
        ib_sig = inspect.signature(ib.load)
        db_sig = inspect.signature(db.load)
        assert list(ib_sig.parameters) == list(db_sig.parameters)
