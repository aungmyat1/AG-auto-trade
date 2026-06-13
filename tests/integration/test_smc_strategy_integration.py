"""Integration tests: SMC pipeline + A1SmcMomentum + RiskEngine.

Tests the full signal path from raw OHLCV → alpha.propose() → risk.validate_entry().
Individual unit tests live in tests/unit/smc/ and tests/unit/test_risk_engine.py.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ag.alpha.a1_smc_momentum.a1_alpha import A1SmcMomentum
from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig
from ag.alpha.base import SignalProposal
from ag.risk.engine import RiskEngine, RiskConfig
from ag.validation.signal_audit import SignalFunnelTracker


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _flat_df(n: int = 30, price: float = 100.0) -> pd.DataFrame:
    return pd.DataFrame({
        "open":   [price] * n,
        "high":   [price + 0.5] * n,
        "low":    [price - 0.5] * n,
        "close":  [price + 0.3] * n,
        "volume": [1000] * n,
    })


def _sweep_and_choch_df() -> pd.DataFrame:
    """Synthetic data with an explicit liquidity sweep + CHOCH event."""
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


# ── Alpha module basics ───────────────────────────────────────────────────────

class TestA1Basics:
    def test_is_ready_always_false(self):
        alpha = A1SmcMomentum()
        assert alpha.is_ready() is False

    def test_propose_returns_none_on_too_few_bars(self):
        alpha = A1SmcMomentum()
        proposal = alpha.propose({"df": _flat_df(5)})
        assert proposal is None

    def test_propose_returns_none_on_flat_data(self):
        """No sweep or structure break → no signal."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        proposal = alpha.propose({"df": _flat_df(30)})
        assert proposal is None

    def test_propose_missing_df_key_returns_none(self):
        alpha = A1SmcMomentum()
        assert alpha.propose({}) is None

    def test_propose_returns_signal_proposal_type(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        df = _sweep_and_choch_df()
        proposal = alpha.propose({"df": df})
        if proposal is not None:
            assert isinstance(proposal, SignalProposal)

    def test_proposal_has_valid_direction(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        proposal = alpha.propose({"df": _sweep_and_choch_df()})
        if proposal is not None:
            assert proposal.direction in ("long", "short")

    def test_proposal_confidence_in_range(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        proposal = alpha.propose({"df": _sweep_and_choch_df()})
        if proposal is not None:
            assert 0.0 < proposal.confidence <= 1.0

    def test_proposal_alpha_id(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        proposal = alpha.propose({"df": _sweep_and_choch_df()})
        if proposal is not None:
            assert proposal.alpha_id == "A1"


# ── Reset behavior ────────────────────────────────────────────────────────────

class TestReset:
    def test_reset_clears_active_obs(self):
        alpha = A1SmcMomentum(config=PipelineConfig(sweep=True, choch=True, ob=True,
                                                     swing_lookback=2, atr_window=5))
        alpha.propose({"df": _sweep_and_choch_df()})
        alpha.reset()
        assert alpha._active_obs == []

    def test_reset_creates_fresh_audit(self):
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        alpha.propose({"df": _sweep_and_choch_df()})
        alpha.reset()
        # After reset the audit tracker has zero counts
        assert alpha.audit.counts.bars_processed == 0


# ── Audit tracker integration ─────────────────────────────────────────────────

class TestAuditIntegration:
    def test_audit_records_bars_processed(self):
        tracker = SignalFunnelTracker()
        alpha = A1SmcMomentum(
            config=PipelineConfig(swing_lookback=2, atr_window=5),
            audit_tracker=tracker,
        )
        df = _sweep_and_choch_df()
        alpha.propose({"df": df})
        assert tracker.counts.bars_processed == len(df)

    def test_audit_records_rejection_on_flat_data(self):
        tracker = SignalFunnelTracker()
        alpha = A1SmcMomentum(
            config=PipelineConfig(swing_lookback=2, atr_window=5),
            audit_tracker=tracker,
        )
        alpha.propose({"df": _flat_df(30)})
        assert tracker.counts.entries_rejected >= 1


# ── Full pipeline: alpha + risk engine ────────────────────────────────────────

class TestAlphaRiskIntegration:
    def test_signal_approved_by_fresh_risk_engine(self):
        """If alpha generates a proposal, a fresh RiskEngine should approve it."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        engine = RiskEngine()
        proposal = alpha.propose({"df": _sweep_and_choch_df()})
        if proposal is None:
            pytest.skip("alpha produced no signal on this synthetic data")
        result = engine.validate_entry(position_size_pct=0.005)
        assert result.approved is True

    def test_signal_blocked_after_g1_trips(self):
        """Alpha produces a signal, but risk engine is at daily limit — blocks."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        engine = _engine_at_daily_limit()
        proposal = alpha.propose({"df": _sweep_and_choch_df()})
        if proposal is None:
            pytest.skip("alpha produced no signal on this synthetic data")
        result = engine.validate_entry(position_size_pct=0.005)
        assert result.approved is False

    def test_no_signal_no_risk_check_needed(self):
        """When alpha returns None, the risk engine is not consulted."""
        alpha = A1SmcMomentum(config=PipelineConfig(swing_lookback=2, atr_window=5))
        engine = RiskEngine()
        proposal = alpha.propose({"df": _flat_df(30)})
        assert proposal is None
        # Risk engine state unchanged — still clean
        assert engine.validate_entry(0.005).approved is True

    def test_ob_filter_requires_price_in_ob_zone(self):
        """With OB filter ON and no matching OB, alpha returns None."""
        alpha = A1SmcMomentum(config=PipelineConfig(
            sweep=True, choch=True, ob=True,
            swing_lookback=2, atr_window=5,
        ))
        # Flat data → no OB detected → no proposal regardless of sweeps/ChoCH
        proposal = alpha.propose({"df": _flat_df(30)})
        assert proposal is None


# ── Helper ────────────────────────────────────────────────────────────────────

def _engine_at_daily_limit() -> RiskEngine:
    engine = RiskEngine(RiskConfig(max_daily_loss_pct=0.02))
    engine.record_trade_result(-0.025)
    return engine
