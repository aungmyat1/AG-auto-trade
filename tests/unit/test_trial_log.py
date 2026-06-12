"""Unit tests for TrialRegistry (ag/validation/trial_log.py)."""
from __future__ import annotations


import pytest

from ag.validation.trial_log import TrialRegistry


@pytest.fixture
def tmp_registry(tmp_path):
    return TrialRegistry(tmp_path / "trials.jsonl")


class TestTrialRegistryLog:
    def test_log_creates_file(self, tmp_registry):
        tmp_registry.log("A0_MVP", "sweep+choch only")
        assert tmp_registry.path.exists()

    def test_log_returns_trial_id(self, tmp_registry):
        tid = tmp_registry.log("A1", "full pipeline")
        assert isinstance(tid, str)
        assert len(tid) == 8

    def test_count_zero_when_no_file(self, tmp_path):
        reg = TrialRegistry(tmp_path / "nonexistent.jsonl")
        assert reg.count("A1") == 0

    def test_count_increments_per_log(self, tmp_registry):
        tmp_registry.log("A0_MVP", "variant 1")
        tmp_registry.log("A0_MVP", "variant 2")
        assert tmp_registry.count("A0_MVP") == 2

    def test_count_is_alpha_specific(self, tmp_registry):
        tmp_registry.log("A0_MVP", "a")
        tmp_registry.log("A1", "b")
        tmp_registry.log("A1", "c")
        assert tmp_registry.count("A0_MVP") == 1
        assert tmp_registry.count("A1") == 2

    def test_params_stored_and_retrieved(self, tmp_registry):
        tmp_registry.log("A0_MVP", "test", params={"lookback": 5, "stop": 0.005})
        entries = tmp_registry.all_trials("A0_MVP")
        assert entries[0].params == {"lookback": 5, "stop": 0.005}

    def test_append_only_does_not_overwrite(self, tmp_registry):
        tmp_registry.log("A1", "first")
        tmp_registry.log("A1", "second")
        entries = tmp_registry.all_trials("A1")
        descriptions = [e.description for e in entries]
        assert "first" in descriptions
        assert "second" in descriptions

    def test_all_trials_no_filter_returns_all(self, tmp_registry):
        tmp_registry.log("A0_MVP", "x")
        tmp_registry.log("A2", "y")
        assert len(tmp_registry.all_trials()) == 2

    def test_all_trials_empty_when_no_file(self, tmp_path):
        reg = TrialRegistry(tmp_path / "none.jsonl")
        assert reg.all_trials() == []


class TestTrialRegistryReport:
    def test_report_no_trials(self, tmp_registry):
        msg = tmp_registry.report("A0_MVP")
        assert "No trials" in msg

    def test_report_lists_entries(self, tmp_registry):
        tmp_registry.log("A0_MVP", "sweep only", params={"lookback": 3})
        report = tmp_registry.report("A0_MVP")
        assert "A0_MVP" in report
        assert "sweep only" in report
        assert "lookback" in report

    def test_report_note_included(self, tmp_registry):
        tmp_registry.log("A1", "full", note="post-IS tuning attempt")
        report = tmp_registry.report("A1")
        assert "post-IS tuning attempt" in report
