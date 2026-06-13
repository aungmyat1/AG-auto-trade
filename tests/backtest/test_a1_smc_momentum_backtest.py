"""Backtest smoke tests for A1SmcMomentum.

Runs A1 bar-by-bar over synthetic OHLCV data and verifies:
  - the module processes data without crashing
  - signal rate and proposal structure match expectations
  - is_ready() is always False (no gate verdict yet)
  - audit funnel is populated
  - reset() produces a clean run

These tests do NOT use Databento data (Phase B, blocked on subscription).
Gate pass requires real data — see scripts/run_gate.py.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.a1_alpha import A1SmcMomentum
from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig
from ag.alpha.base import SignalProposal


# ── Synthetic data helpers ────────────────────────────────────────────────────

def _flat_df(n: int = 50, price: float = 100.0) -> pd.DataFrame:
    return pd.DataFrame({
        "open":   [price] * n,
        "high":   [price + 0.5] * n,
        "low":    [price - 0.5] * n,
        "close":  [price + 0.3] * n,
        "volume": [1000] * n,
    })


def _sweep_and_choch_df() -> pd.DataFrame:
    """30-bar synthetic with a liquidity sweep + CHOCH to exercise the MVP config."""
    opens  = [100]*3 + [104, 108, 111, 109, 106, 104, 108, 111, 109, 106,
                        112, 110, 108, 105, 103, 100, 102, 105]
    highs  = [101]*3 + [108, 112, 115, 109, 108, 108, 112, 115, 109, 106,
                        118, 109, 106, 103, 101,  98, 101, 104]
    lows   = [99] *3 + [103, 107, 110, 107, 104, 103, 107, 110, 107, 104,
                        111, 106, 103, 101,  98,  95,  99, 102]
    closes = [100]*3 + [106, 110, 112, 108, 106, 106, 110, 112, 108, 105,
                        114, 108, 104, 102, 100,  96, 101, 103]
    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows, "close": closes,
        "volume": [1000] * len(opens),
    })


def _run_bar_by_bar(alpha: A1SmcMomentum, df: pd.DataFrame,
                    min_window: int = 10) -> list[SignalProposal]:
    """Simulate a streaming backtest: feed growing windows to propose()."""
    signals = []
    for i in range(min_window, len(df) + 1):
        window = df.iloc[:i].copy()
        proposal = alpha.propose({"df": window})
        if proposal is not None:
            signals.append(proposal)
    return signals


# ── Smoke tests ───────────────────────────────────────────────────────────────

class TestA1BacktestSmoke:
    def test_runs_without_exception_on_flat_data(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        signals = _run_bar_by_bar(alpha, _flat_df(50))
        assert isinstance(signals, list)

    def test_runs_without_exception_on_sweep_choch_data(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        signals = _run_bar_by_bar(alpha, _sweep_and_choch_df())
        assert isinstance(signals, list)

    def test_no_signals_on_flat_data(self):
        """Flat market should produce no sweep or CHOCH → zero signals."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        signals = _run_bar_by_bar(alpha, _flat_df(50))
        assert signals == []

    def test_all_proposals_have_valid_structure(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        signals = _run_bar_by_bar(alpha, _sweep_and_choch_df())
        for s in signals:
            assert isinstance(s, SignalProposal)
            assert s.direction in ("long", "short")
            assert 0.0 < s.confidence <= 1.0
            assert s.alpha_id == "A1"
            assert s.stop_distance_pct > 0
            assert s.target_distance_pct > 0

    def test_is_ready_always_false_during_backtest(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        df = _sweep_and_choch_df()
        for i in range(10, len(df) + 1):
            alpha.propose({"df": df.iloc[:i]})
            assert alpha.is_ready() is False


# ── Audit tracking ────────────────────────────────────────────────────────────

class TestAuditAfterBacktest:
    def test_audit_bars_processed_equals_total_bars_fed(self):
        """Sum of bars across all propose() calls = counts.bars_processed."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        df = _sweep_and_choch_df()
        expected_bars = sum(range(10, len(df) + 1))
        _run_bar_by_bar(alpha, df)
        assert alpha.audit.counts.bars_processed == expected_bars

    def test_audit_has_rejections_on_flat_data(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        _run_bar_by_bar(alpha, _flat_df(30))
        assert alpha.audit.counts.entries_rejected > 0

    def test_reset_restores_clean_audit(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        _run_bar_by_bar(alpha, _sweep_and_choch_df())
        alpha.reset()
        assert alpha.audit.counts.bars_processed == 0
        assert alpha.audit.counts.entries_rejected == 0


# ── Reset between runs ────────────────────────────────────────────────────────

class TestResetBetweenRuns:
    def test_two_independent_runs_same_signal_count(self):
        """reset() ensures a second run is identical to the first."""
        cfg = PipelineConfig(swing_lookback=2, atr_window=5)
        df = _sweep_and_choch_df()

        alpha = A1SmcMomentum(config=cfg)
        signals_run1 = _run_bar_by_bar(alpha, df)

        alpha.reset()
        signals_run2 = _run_bar_by_bar(alpha, df)

        assert len(signals_run1) == len(signals_run2)

    def test_ob_accumulation_cleared_by_reset(self):
        """Active OBs from run 1 must not contaminate run 2 after reset."""
        cfg = PipelineConfig(sweep=True, choch=True, ob=True,
                             swing_lookback=2, atr_window=5)
        alpha = A1SmcMomentum(config=cfg)
        _run_bar_by_bar(alpha, _sweep_and_choch_df())
        alpha.reset()
        assert alpha._active_obs == []


# ── Signal rate sanity ────────────────────────────────────────────────────────

class TestSignalRate:
    def test_signal_rate_not_100_percent(self):
        """Alpha must not fire on every bar — that would indicate a logic error."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        df = _sweep_and_choch_df()
        signals = _run_bar_by_bar(alpha, df)
        total_bars = len(df) - 10 + 1
        signal_rate = len(signals) / total_bars if total_bars > 0 else 0
        assert signal_rate < 1.0, f"Signal rate {signal_rate:.0%} is suspiciously high"

    def test_additional_filters_reduce_signal_rate(self):
        """Enabling OB + FVG must not increase signal rate over sweep+choch only."""
        df = _sweep_and_choch_df()
        cfg_base = PipelineConfig(sweep=True, choch=True, swing_lookback=2, atr_window=5)
        cfg_full = PipelineConfig(sweep=True, choch=True, ob=True, fvg=True,
                                  swing_lookback=2, atr_window=5)

        alpha_base = A1SmcMomentum(config=cfg_base)
        alpha_full = A1SmcMomentum(config=cfg_full)

        signals_base = _run_bar_by_bar(alpha_base, df)
        signals_full = _run_bar_by_bar(alpha_full, df)

        assert len(signals_full) <= len(signals_base)
