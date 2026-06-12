"""Unit tests for SignalFunnelTracker."""
from __future__ import annotations

import pytest

from ag.validation.signal_audit import SignalFunnelTracker, RejectionReason


class TestRecord:
    def test_increments_valid_event(self):
        t = SignalFunnelTracker()
        t.record("sweeps_detected", 5)
        assert t.counts.sweeps_detected == 5

    def test_defaults_to_1(self):
        t = SignalFunnelTracker()
        t.record("bos_detected")
        assert t.counts.bos_detected == 1

    def test_accumulates_across_calls(self):
        t = SignalFunnelTracker()
        t.record("choch_detected", 3)
        t.record("choch_detected", 4)
        assert t.counts.choch_detected == 7

    def test_invalid_event_raises(self):
        t = SignalFunnelTracker()
        with pytest.raises(ValueError, match="Unknown event"):
            t.record("not_a_real_event")


class TestReject:
    def test_increments_entries_rejected(self):
        t = SignalFunnelTracker()
        t.reject(RejectionReason.REGIME_FAIL)
        assert t.counts.entries_rejected == 1

    def test_stores_reason(self):
        t = SignalFunnelTracker()
        t.reject(RejectionReason.REGIME_FAIL, 3)
        assert t.rejection_breakdown()[RejectionReason.REGIME_FAIL] == 3

    def test_multiple_reasons(self):
        t = SignalFunnelTracker()
        t.reject(RejectionReason.REGIME_FAIL, 10)
        t.reject(RejectionReason.ATR_FLOOR, 5)
        bd = t.rejection_breakdown()
        assert bd[RejectionReason.REGIME_FAIL] == 10
        assert bd[RejectionReason.ATR_FLOOR] == 5
        assert t.counts.entries_rejected == 15


class TestConversionRate:
    def test_zero_when_no_entries(self):
        t = SignalFunnelTracker()
        assert t.conversion_rate() == 0.0

    def test_correct_rate(self):
        t = SignalFunnelTracker()
        t.record("entries_generated", 10)
        t.record("trades_executed", 7)
        assert t.conversion_rate() == pytest.approx(0.7)

    def test_can_exceed_one_if_miscounted(self):
        t = SignalFunnelTracker()
        t.record("entries_generated", 1)
        t.record("trades_executed", 2)
        assert t.conversion_rate() == pytest.approx(2.0)


class TestSummary:
    def test_summary_has_counts_key(self):
        t = SignalFunnelTracker()
        s = t.summary()
        assert "counts" in s
        assert "rejection_reasons" in s
        assert "conversion_rate" in s

    def test_summary_counts_match_record(self):
        t = SignalFunnelTracker()
        t.record("obs_detected", 8)
        assert t.summary()["counts"]["obs_detected"] == 8


class TestReport:
    def test_report_contains_funnel_labels(self):
        t = SignalFunnelTracker()
        t.record("sweeps_detected", 1248)
        t.record("choch_detected", 338)
        rpt = t.report()
        assert "1,248" in rpt
        assert "338" in rpt
        assert "Signal Funnel Report" in rpt

    def test_report_includes_rejection_breakdown(self):
        t = SignalFunnelTracker()
        t.reject(RejectionReason.REGIME_FAIL, 7)
        rpt = t.report()
        assert RejectionReason.REGIME_FAIL in rpt
        assert "7" in rpt

    def test_report_no_breakdown_when_no_rejections(self):
        t = SignalFunnelTracker()
        rpt = t.report()
        assert "Rejection breakdown" not in rpt


class TestBottleneck:
    def test_identifies_largest_dropoff(self):
        t = SignalFunnelTracker()
        # bars → sweeps: 500 → 495 (drop = 5)
        # sweeps → choch: 495 → 490 (drop = 5)
        # choch → where_active: 490 → 2 (drop = 488) ← largest
        t.record("bars_processed", 500)
        t.record("sweeps_detected", 495)
        t.record("choch_detected", 490)
        t.record("where_signals_active", 2)
        t.record("entries_generated", 2)
        t.record("trades_executed", 2)
        assert t.bottleneck() == "choch → where_active"

    def test_bottleneck_with_no_data(self):
        t = SignalFunnelTracker()
        # Should not raise — just pick the first stage
        result = t.bottleneck()
        assert isinstance(result, str)
