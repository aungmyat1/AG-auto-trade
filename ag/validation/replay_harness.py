"""
Replay harness + look-ahead verification utilities — STRATEGY-AGNOSTIC.

The job here is not to test any strategy. It is to make it *impossible* for a
strategy to pass validation because of a testing flaw: future-candle leakage,
repainting, or timestamp misalignment. A backtest from a peeking detector is
worthless; these utilities prove the detector cannot peek.

Two guarantees, both requiring NO market data (synthetic bars only):

  1. ReplayHarness feeds OHLCV one bar at a time and exposes ONLY history up to
     and including the current closed bar — never bar i+1. Deterministic.

  2. future_leak_free() / repaint_free() are property checks that run a detector
     on clean vs future-poisoned (and on growing prefixes) and verify that
     detections about the PAST do not change when the FUTURE changes.

Detector contract assumed: callable `detect(df) -> list[obj]` where every obj has
an integer `.bar_index` (formation bar) and is a dataclass. Mutable-state fields
(`mitigated`, `sweep_confirmed`) legitimately evolve as bars arrive and are
EXCLUDED from identity — changing them is not repainting.
"""
from __future__ import annotations

import dataclasses
from typing import Callable, Iterator, Protocol, Sequence

import pandas as pd


# Fields that legitimately change as later bars arrive (mitigation is forward
# information, not a repaint of the original detection).
_STATE_FIELDS = frozenset({"mitigated", "sweep_confirmed"})

# Default number of bars near a split that may still be "forming" / awaiting
# confirmation, and are therefore allowed to differ. Past this buffer a detection
# must be stable.
DEFAULT_CONFIRM_BUFFER = 5


class Detector(Protocol):
    def detect(self, df: pd.DataFrame) -> Sequence: ...


DetectFn = Callable[[pd.DataFrame], Sequence]


# ──────────────────────────────────────────────────────────────────────────────
# Replay harness
# ──────────────────────────────────────────────────────────────────────────────

class FutureAccessError(AssertionError):
    """Raised if anything attempts to read beyond the current bar."""


class ReplayHarness:
    """
    Feed OHLCV bar-by-bar. The callback only ever sees `df.iloc[:i+1]`.

    Usage:
        harness = ReplayHarness(df, warmup=20)
        for i, history in harness.stream():
            proposal = strategy_on_window(history)   # history has no future bars
        # or:
        harness.run(lambda i, history: strategy_on_window(history))

    Invariants enforced:
      • timestamps (index or 'timestamp' col) are strictly monotonic increasing;
      • the window handed out never contains a bar later than the current one;
      • iteration is deterministic and position-based.
    """

    def __init__(self, df: pd.DataFrame, warmup: int = 1) -> None:
        if warmup < 1:
            raise ValueError("warmup must be >= 1")
        if len(df) < warmup:
            raise ValueError(f"need >= warmup ({warmup}) bars, got {len(df)}")
        self._validate_timestamps(df)
        self._df = df
        self.warmup = warmup

    @staticmethod
    def _validate_timestamps(df: pd.DataFrame) -> None:
        ts = None
        if isinstance(df.index, pd.DatetimeIndex):
            ts = df.index
        elif "timestamp" in df.columns:
            ts = pd.DatetimeIndex(df["timestamp"])
        if ts is not None and not ts.is_monotonic_increasing:
            raise FutureAccessError("timestamps are not monotonically increasing")
        if ts is not None and ts.has_duplicates:
            raise FutureAccessError("duplicate timestamps present")

    def stream(self) -> Iterator[tuple[int, pd.DataFrame]]:
        n = len(self._df)
        for i in range(self.warmup - 1, n):
            # history = closed bars 0..i inclusive. A defensive copy so a
            # callback cannot mutate the source and cannot be handed i+1.
            yield i, self._df.iloc[: i + 1].copy()

    def run(self, on_bar: Callable[[int, pd.DataFrame], object]) -> list:
        return [on_bar(i, hist) for i, hist in self.stream()]


# ──────────────────────────────────────────────────────────────────────────────
# Concept identity (mitigation-agnostic)
# ──────────────────────────────────────────────────────────────────────────────

def concept_key(obj, ndigits: int = 6) -> tuple:
    """Stable identity of a detected concept, ignoring mutable-state fields."""
    if not dataclasses.is_dataclass(obj):
        raise TypeError(f"{type(obj).__name__} is not a dataclass concept")
    items = []
    for f in dataclasses.fields(obj):
        if f.name in _STATE_FIELDS:
            continue
        v = getattr(obj, f.name)
        items.append((f.name, round(v, ndigits) if isinstance(v, float) else v))
    return (type(obj).__name__, tuple(sorted(items)))


def _keys(objs: Sequence, *, upto_bar: int | None = None) -> set:
    if upto_bar is None:
        return {concept_key(o) for o in objs}
    return {concept_key(o) for o in objs if getattr(o, "bar_index") <= upto_bar}


# ──────────────────────────────────────────────────────────────────────────────
# Future poisoning + leak/repaint checks
# ──────────────────────────────────────────────────────────────────────────────

def poison_future(df: pd.DataFrame, split: int, *, offset: float = 1_000.0) -> pd.DataFrame:
    """
    Return a copy of df whose bars AFTER `split` are replaced with clearly
    different (but finite) prices. A correct detector's output for bars <= split
    is unaffected; a peeking one changes. Finite (not NaN) so detectors don't
    crash — leakage must be caught by changed output, not by an exception.
    """
    out = df.copy()
    fut = out.index[split + 1:]
    for col in ("open", "high", "low", "close"):
        if col in out.columns:
            out.loc[fut, col] = out.loc[fut, col] + offset
    return out


def future_leak_free(
    detect_fn: DetectFn,
    df: pd.DataFrame,
    split: int,
    *,
    confirm_buffer: int = DEFAULT_CONFIRM_BUFFER,
) -> bool:
    """
    True iff detections about bars <= (split - confirm_buffer) are identical
    whether or not the future (bars > split) is poisoned. False ⇒ look-ahead.
    """
    horizon = split - confirm_buffer
    clean = _keys(detect_fn(df), upto_bar=horizon)
    poisoned = _keys(detect_fn(poison_future(df, split)), upto_bar=horizon)
    return clean == poisoned


def repaint_free(
    detect_fn: DetectFn,
    df: pd.DataFrame,
    splits: Sequence[int],
    *,
    confirm_buffer: int = DEFAULT_CONFIRM_BUFFER,
) -> bool:
    """
    True iff every detection confirmed on a prefix df[:k] still exists, unchanged,
    when the full series is processed. False ⇒ the detector repaints past zones.
    """
    full = _keys(detect_fn(df))
    for k in splits:
        prefix_past = _keys(detect_fn(df.iloc[:k]), upto_bar=k - confirm_buffer)
        if not prefix_past <= full:
            return False
    return True
