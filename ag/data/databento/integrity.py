"""Data integrity checks for OHLCV DataFrames.

Run these checks after loading from cache or after a fresh download — before
any bar ever reaches an alpha module or the gate. A single corrupt bar (e.g.
H < L, a CME session gap, a duplicate timestamp) can produce fake SMC signals.

Usage:
    from ag.data.databento.integrity import check_ohlcv, IntegrityError

    report = check_ohlcv(df, symbol="GC", timeframe="1h")
    if not report.passed:
        raise IntegrityError(report.summary())

Checks performed:
  C1  Minimum bar count
  C2  Required columns present (open, high, low, close, volume)
  C3  UTC DatetimeIndex with no naivety
  C4  Monotonically increasing timestamps (no duplicates)
  C5  OHLC consistency: high >= open, close; low <= open, close; high >= low
  C6  No negative prices or volumes
  C7  Gap detection: warns on runs of missing CME session bars > MAX_GAP_BARS
  C8  No NaN / Inf values in OHLC columns
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────

MIN_BARS = 100          # fewer than this = not enough to compute meaningful indicators
MAX_GAP_BARS = 10       # warn if any gap exceeds this many consecutive missing bars


# ── Types ─────────────────────────────────────────────────────────────────────

class IntegrityError(ValueError):
    """Raised when a hard check fails (errors, not warnings)."""


@dataclass
class IntegrityReport:
    symbol: str
    timeframe: str
    n_bars: int
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [
            f"[{status}] Integrity check — {self.symbol} {self.timeframe}  ({self.n_bars:,} bars)",
        ]
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING {w}")
        if not self.errors and not self.warnings:
            lines.append("  All checks clean.")
        return "\n".join(lines)


# ── Public entry point ────────────────────────────────────────────────────────

def check_ohlcv(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    min_bars: int = MIN_BARS,
    max_gap_bars: int = MAX_GAP_BARS,
) -> IntegrityReport:
    """Run all integrity checks on an OHLCV DataFrame.

    Returns an IntegrityReport. Does NOT raise — callers decide whether to
    raise IntegrityError based on report.passed.
    """
    errors: list[str] = []
    warnings: list[str] = []
    n = len(df)

    # C1 — minimum bars
    if n < min_bars:
        errors.append(f"C1 too few bars: {n} < {min_bars}")

    # C2 — required columns
    required = {"open", "high", "low", "close", "volume"}
    missing_cols = required - set(df.columns)
    if missing_cols:
        errors.append(f"C2 missing columns: {sorted(missing_cols)}")
        # Cannot continue most checks without OHLC columns
        return IntegrityReport(symbol, timeframe, n, False, errors, warnings)

    # C3 — UTC DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        errors.append("C3 index is not DatetimeIndex")
    elif df.index.tz is None:
        errors.append("C3 index is timezone-naive (expected UTC)")
    elif str(df.index.tz) != "UTC":
        warnings.append(f"C3 index timezone is {df.index.tz}, not UTC")

    # C4 — monotonically increasing, no duplicates
    if isinstance(df.index, pd.DatetimeIndex):
        if not df.index.is_monotonic_increasing:
            errors.append("C4 timestamps are not monotonically increasing")
        dupes = df.index.duplicated().sum()
        if dupes:
            errors.append(f"C4 {dupes} duplicate timestamp(s) found")

    # C5 — OHLC consistency
    bad_hl = (df["high"] < df["low"]).sum()
    bad_ho = (df["high"] < df["open"]).sum()
    bad_hc = (df["high"] < df["close"]).sum()
    bad_lo = (df["low"] > df["open"]).sum()
    bad_lc = (df["low"] > df["close"]).sum()
    ohlc_violations = bad_hl + bad_ho + bad_hc + bad_lo + bad_lc
    if ohlc_violations:
        errors.append(
            f"C5 OHLC violations: H<L={bad_hl}, H<O={bad_ho}, H<C={bad_hc}, "
            f"L>O={bad_lo}, L>C={bad_lc}"
        )

    # C6 — no negative prices or volumes
    for col in ("open", "high", "low", "close"):
        neg = (df[col] <= 0).sum()
        if neg:
            errors.append(f"C6 {neg} non-positive value(s) in '{col}'")
    neg_vol = (df["volume"] < 0).sum()
    if neg_vol:
        errors.append(f"C6 {neg_vol} negative volume value(s)")

    # C7 — gap detection (warn only, not an error)
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 1:
        gaps = _detect_gaps(df, timeframe, max_gap_bars)
        if gaps:
            warnings.append(
                f"C7 {len(gaps)} gap(s) > {max_gap_bars} bars: "
                + ", ".join(f"{g[0].date()} ({g[1]} bars)" for g in gaps[:3])
                + (" …" if len(gaps) > 3 else "")
            )

    # C8 — no NaN/Inf in OHLCV
    for col in ("open", "high", "low", "close", "volume"):
        bad = int(df[col].isna().sum()) + int(np.isinf(df[col]).sum())
        if bad:
            errors.append(f"C8 {bad} NaN/Inf value(s) in '{col}'")

    passed = len(errors) == 0
    return IntegrityReport(symbol, timeframe, n, passed, errors, warnings)


# ── Gap detection helper ──────────────────────────────────────────────────────

_EXPECTED_FREQ = {
    "1m": pd.Timedelta("1min"),
    "1h": pd.Timedelta("1h"),
}


def _detect_gaps(
    df: pd.DataFrame,
    timeframe: str,
    max_gap_bars: int,
) -> list[tuple[pd.Timestamp, int]]:
    """Return list of (gap_start_timestamp, gap_size_in_bars) for gaps > max_gap_bars."""
    freq = _EXPECTED_FREQ.get(timeframe)
    if freq is None:
        return []

    gaps = []
    diffs = df.index.to_series().diff().dropna()
    for ts, delta in diffs.items():
        missing = int(delta / freq) - 1
        if missing > max_gap_bars:
            gaps.append((ts, missing))
    return gaps
