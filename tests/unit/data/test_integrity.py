"""Unit tests for check_ohlcv() — all 8 integrity checks.

Uses synthetic fixtures with controllable defect injection; no API calls needed.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.data.databento.integrity import check_ohlcv, IntegrityReport, IntegrityError
from tests.fixtures.synthetic import make_gc_1h, make_ohlcv


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean(n_bars: int = 200) -> pd.DataFrame:
    return make_gc_1h(n_bars=n_bars)


def _check(df: pd.DataFrame, **kwargs) -> IntegrityReport:
    return check_ohlcv(df, symbol="GC", timeframe="1h", **kwargs)


# ── C1: minimum bar count ─────────────────────────────────────────────────────

class TestC1MinBars:
    def test_passes_with_enough_bars(self):
        r = _check(_clean(200), min_bars=100)
        assert r.passed

    def test_fails_when_too_few_bars(self):
        df = _clean(50)
        r = _check(df, min_bars=100)
        assert not r.passed
        assert any("C1" in e for e in r.errors)

    def test_n_bars_reported_correctly(self):
        df = _clean(150)
        r = _check(df)
        assert r.n_bars == 150

    def test_custom_min_bars(self):
        df = _clean(30)
        r = _check(df, min_bars=20)
        assert r.passed


# ── C2: required columns ──────────────────────────────────────────────────────

class TestC2RequiredColumns:
    def test_passes_with_all_columns(self):
        r = _check(_clean())
        assert r.passed

    def test_fails_when_volume_missing(self):
        df = _clean().drop(columns=["volume"])
        r = _check(df)
        assert not r.passed
        assert any("C2" in e for e in r.errors)

    def test_fails_when_multiple_columns_missing(self):
        df = _clean().drop(columns=["high", "low"])
        r = _check(df)
        assert not r.passed
        missing_text = next(e for e in r.errors if "C2" in e)
        assert "high" in missing_text or "low" in missing_text

    def test_early_return_on_missing_columns(self):
        """No further checks should run if OHLC columns are absent."""
        df = _clean().drop(columns=["open", "high", "low", "close", "volume"])
        r = _check(df)
        assert not r.passed
        assert len(r.errors) == 1  # only C2, not downstream errors


# ── C3: UTC DatetimeIndex ─────────────────────────────────────────────────────

class TestC3UTCIndex:
    def test_passes_with_utc_index(self):
        r = _check(_clean())
        assert r.passed

    def test_fails_when_index_is_naive(self):
        df = _clean()
        df.index = df.index.tz_localize(None)
        r = _check(df)
        assert not r.passed
        assert any("C3" in e for e in r.errors)

    def test_warns_when_timezone_is_not_utc(self):
        df = _clean()
        df.index = df.index.tz_convert("US/Eastern")
        r = _check(df)
        assert any("C3" in w for w in r.warnings)

    def test_passes_when_index_not_datetimeindex_triggers_c3_error(self):
        df = _clean().reset_index(drop=True)  # integer index
        r = _check(df)
        assert not r.passed
        assert any("C3" in e for e in r.errors)


# ── C4: monotonic, no duplicates ──────────────────────────────────────────────

class TestC4Monotonic:
    def test_passes_clean_data(self):
        r = _check(_clean())
        assert r.passed

    def test_fails_with_duplicate_timestamps(self):
        df = make_gc_1h(with_duplicates=True)
        r = _check(df, min_bars=50)
        assert not r.passed
        assert any("C4" in e and "duplicate" in e.lower() for e in r.errors)

    def test_fails_when_not_monotonic(self):
        df = _clean()
        # Swap two rows to break monotonicity without duplicating
        idx = df.index.tolist()
        idx[10], idx[11] = idx[11], idx[10]
        df.index = pd.DatetimeIndex(idx, tz="UTC")
        r = _check(df)
        assert not r.passed
        assert any("C4" in e for e in r.errors)

    def test_duplicate_count_in_error_message(self):
        df = make_gc_1h(with_duplicates=True)
        r = _check(df, min_bars=50)
        dup_errors = [e for e in r.errors if "C4" in e and "duplicate" in e.lower()]
        assert len(dup_errors) == 1


# ── C5: OHLC consistency ──────────────────────────────────────────────────────

class TestC5OHLCConsistency:
    def test_passes_clean_data(self):
        r = _check(_clean())
        assert r.passed

    def test_fails_when_high_below_low(self):
        df = make_gc_1h(with_ohlc_violation=True)
        r = _check(df)
        assert not r.passed
        assert any("C5" in e for e in r.errors)

    def test_c5_error_mentions_hl_count(self):
        df = make_gc_1h(with_ohlc_violation=True)
        r = _check(df)
        c5 = next(e for e in r.errors if "C5" in e)
        assert "H<L" in c5

    def test_manually_injected_high_below_open(self):
        df = _clean(200)
        df.iloc[5, df.columns.get_loc("high")] = df.iloc[5]["open"] - 10.0
        r = _check(df)
        assert not r.passed
        assert any("C5" in e for e in r.errors)


# ── C6: no negative prices or volumes ────────────────────────────────────────

class TestC6NonNegative:
    def test_passes_clean_data(self):
        r = _check(_clean())
        assert r.passed

    def test_fails_with_negative_close(self):
        df = _clean()
        df.iloc[10, df.columns.get_loc("close")] = -1.0
        r = _check(df)
        assert not r.passed
        assert any("C6" in e and "close" in e for e in r.errors)

    def test_fails_with_zero_open(self):
        df = _clean()
        df.iloc[5, df.columns.get_loc("open")] = 0.0
        r = _check(df)
        assert not r.passed
        assert any("C6" in e and "open" in e for e in r.errors)

    def test_fails_with_negative_volume(self):
        df = _clean()
        df.iloc[20, df.columns.get_loc("volume")] = -500.0
        r = _check(df)
        assert not r.passed
        assert any("C6" in e and "volume" in e for e in r.errors)


# ── C7: gap detection (warning only) ─────────────────────────────────────────

class TestC7GapDetection:
    def test_no_warning_for_clean_data(self):
        df = _clean(300)
        r = _check(df)
        assert not any("C7" in w for w in r.warnings)
        assert r.passed

    def test_warns_on_injected_gap(self):
        df = make_gc_1h(n_bars=300, with_gap=True)
        # with_gap injects a 20-bar gap; default max_gap_bars=10
        r = _check(df, min_bars=50, max_gap_bars=10)
        assert any("C7" in w for w in r.warnings)

    def test_gap_warning_does_not_fail_report(self):
        df = make_gc_1h(n_bars=300, with_gap=True)
        r = _check(df, min_bars=50, max_gap_bars=10)
        assert r.passed  # gaps are warnings, not errors

    def test_no_warning_when_gap_within_threshold(self):
        df = make_gc_1h(n_bars=300, with_gap=True)
        # max_gap_bars=30 — the injected 20-bar gap is within threshold
        r = _check(df, min_bars=50, max_gap_bars=30)
        assert not any("C7" in w for w in r.warnings)


# ── C8: NaN / Inf values ─────────────────────────────────────────────────────

class TestC8NaNInf:
    def test_passes_clean_data(self):
        r = _check(_clean())
        assert r.passed

    def test_fails_with_nan_in_close(self):
        df = make_gc_1h(with_nan=True)
        r = _check(df)
        assert not r.passed
        assert any("C8" in e and "close" in e for e in r.errors)

    def test_fails_with_inf_in_open(self):
        df = _clean()
        df.iloc[10, df.columns.get_loc("open")] = float("inf")
        r = _check(df)
        assert not r.passed
        assert any("C8" in e for e in r.errors)

    def test_fails_with_negative_inf(self):
        df = _clean()
        df.iloc[10, df.columns.get_loc("high")] = float("-inf")
        r = _check(df)
        assert not r.passed
        assert any("C8" in e for e in r.errors)


# ── IntegrityReport.summary() ─────────────────────────────────────────────────

class TestSummary:
    def test_summary_pass_prefix(self):
        r = _check(_clean())
        assert r.summary().startswith("[PASS]")

    def test_summary_fail_prefix(self):
        df = _clean(10)  # too few bars
        r = _check(df)
        assert r.summary().startswith("[FAIL]")

    def test_summary_includes_symbol_and_timeframe(self):
        r = check_ohlcv(_clean(), symbol="GC", timeframe="1h")
        assert "GC" in r.summary()
        assert "1h" in r.summary()

    def test_summary_includes_bar_count(self):
        df = _clean(200)
        r = _check(df)
        assert "200" in r.summary()

    def test_summary_lists_errors(self):
        df = _clean(10)
        r = _check(df)
        assert "ERROR" in r.summary()

    def test_summary_clean_message_when_no_issues(self):
        r = _check(_clean())
        assert "All checks clean." in r.summary()


# ── IntegrityError ────────────────────────────────────────────────────────────

class TestIntegrityError:
    def test_is_value_error_subclass(self):
        assert issubclass(IntegrityError, ValueError)

    def test_raise_from_report_summary(self):
        df = _clean(10)
        r = _check(df)
        with pytest.raises(IntegrityError, match="C1"):
            raise IntegrityError(r.summary())
