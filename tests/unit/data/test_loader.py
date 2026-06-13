"""Unit tests for DatabentoLoader — offline / cache paths only.

No Databento API calls are made. Tests use synthetic parquet fixtures written
to a temp directory to exercise the full cache read/write/validate path.
"""
from __future__ import annotations

import os
import pathlib

import pandas as pd
import pytest

from ag.data.databento.loader import (
    DatabentoLoader,
    DatabentoKeyMissingError,
    UnsupportedSymbolError,
    UnsupportedTimeframeError,
    SUPPORTED_SYMBOLS,
)
from tests.fixtures.synthetic import make_gc_1h, save_fixture


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / "cache"


@pytest.fixture
def loader(cache_dir):
    return DatabentoLoader(cache_dir=cache_dir)


@pytest.fixture
def seeded_cache(cache_dir):
    """Write a synthetic GC 1h parquet into the temp cache dir."""
    pytest.importorskip("pyarrow", reason="pyarrow required for parquet cache")
    df = make_gc_1h(n_bars=500)
    save_fixture(df, cache_dir / "GC_1h.parquet")
    return cache_dir


# ── Cache hit path ────────────────────────────────────────────────────────────

class TestCacheHit:
    def test_returns_dataframe_from_cache(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 500

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

    def test_cache_hit_does_not_require_api_key(self, loader, seeded_cache, monkeypatch):
        monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")
        assert len(df) > 0

    def test_cache_hit_does_not_require_start_end(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        df = loader.load("GC", "1h")  # no start/end — should work from cache
        assert len(df) > 0


# ── Cache miss path ───────────────────────────────────────────────────────────

class TestCacheMiss:
    def test_miss_without_start_raises_value_error(self, loader):
        with pytest.raises(ValueError, match="start="):
            loader.load("GC", "1h")  # no start/end, no cache

    def test_miss_without_api_key_raises_key_error(self, loader, monkeypatch):
        monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
        with pytest.raises(DatabentoKeyMissingError):
            loader.load("GC", "1h", start="2023-01-01", end="2023-12-31")

    def test_miss_with_api_key_but_no_package_raises_package_error(
        self, loader, monkeypatch
    ):
        monkeypatch.setenv("DATABENTO_API_KEY", "dummy_key")
        import sys
        # Temporarily hide the databento package if installed
        saved = sys.modules.get("databento")
        sys.modules["databento"] = None  # type: ignore[assignment]
        try:
            with pytest.raises((ImportError, TypeError)):
                loader.load("GC", "1h", start="2023-01-01", end="2023-12-31")
        finally:
            if saved is None:
                del sys.modules["databento"]
            else:
                sys.modules["databento"] = saved


# ── cache_exists / cache_path ─────────────────────────────────────────────────

class TestCacheHelpers:
    def test_cache_exists_false_before_seeding(self, loader):
        assert loader.cache_exists("GC", "1h") is False

    def test_cache_exists_true_after_seeding(self, loader, seeded_cache):
        loader.cache_dir = seeded_cache
        assert loader.cache_exists("GC", "1h") is True

    def test_cache_path_returns_expected_filename(self, loader):
        p = loader.cache_path("GC", "1h")
        assert p.name == "GC_1h.parquet"

    def test_cache_path_for_mgc(self, loader):
        p = loader.cache_path("MGC", "1m")
        assert p.name == "MGC_1m.parquet"


# ── Validation ────────────────────────────────────────────────────────────────

class TestValidation:
    def test_invalid_symbol_raises(self, loader):
        with pytest.raises(UnsupportedSymbolError):
            loader.load("BTC", "1h")

    def test_invalid_timeframe_raises(self, loader):
        with pytest.raises(UnsupportedTimeframeError):
            loader.load("GC", "4h")

    def test_all_supported_symbols_validate(self, loader, seeded_cache):
        """Every symbol in SUPPORTED_SYMBOLS passes the validator."""
        for sym in SUPPORTED_SYMBOLS:
            # Just check validation doesn't raise — no cache needed
            loader._validate(sym, "1h")

    def test_supported_timeframes_validate(self, loader):
        for tf in ("1m", "1h"):
            loader._validate("GC", tf)


# ── write-then-read roundtrip ─────────────────────────────────────────────────

class TestRoundtrip:
    @pytest.fixture(autouse=True)
    def _require_pyarrow(self):
        pytest.importorskip("pyarrow", reason="pyarrow required for parquet cache")

    def test_write_cache_then_read_back(self, loader):
        df_in = make_gc_1h(n_bars=300)
        path = loader.cache_dir / "GC_1h.parquet"
        loader._write_cache(df_in, path)
        df_out = loader._read_cache(path)
        assert len(df_out) == 300
        assert list(df_out.columns) == list(df_in.columns)

    def test_roundtrip_preserves_utc_index(self, loader):
        df_in = make_gc_1h(n_bars=100)
        path = loader.cache_dir / "GC_1h.parquet"
        loader._write_cache(df_in, path)
        df_out = loader._read_cache(path)
        assert str(df_out.index.tz) == "UTC"

    def test_roundtrip_preserves_values(self, loader):
        df_in = make_gc_1h(n_bars=50)
        path = loader.cache_dir / "GC_1h.parquet"
        loader._write_cache(df_in, path)
        df_out = loader._read_cache(path)
        pd.testing.assert_frame_equal(df_in, df_out, check_like=True)
