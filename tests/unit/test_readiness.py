"""Tests for TRGSDecisionEngine — 6-state deployment readiness ladder."""
from __future__ import annotations

import json
import random

import pytest

from ag.validation.gate import CheckResult, GateResult
from ag.validation.edge_validator import EdgeResult
from ag.validation.readiness import ReadinessStatus, TRGSDecisionEngine, TRGSReport

TIMESTAMP = "2026-06-14T00:00:00Z"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _gate_result(verdict: str, n: int = 500, dd: float = 0.08, pf_net: float = 1.30) -> GateResult:
    checks = [
        CheckResult("n >= 50",         n >= 50,        float(n), 50,   ">="),
        CheckResult("gross PF > 1.0",  True,           1.5,      1.0         ),
        CheckResult("n >= 200",        n >= 200,       float(n), 200,  ">="),
        CheckResult("net PF > 1.25",   pf_net > 1.25,  pf_net,   1.25        ),
        CheckResult("win rate > 45%",  True,           0.50,     0.45        ),
        CheckResult("Sharpe > 1.2",    True,           1.5,      1.2         ),
        CheckResult("max DD < 15%",    dd < 0.15,      dd,       0.15,   "<" ),
        CheckResult("CPCV median PF > 1.0", True,      1.1,      1.0         ),
        CheckResult("WF pass rate >= 60%",  True,      0.75,     0.60,  ">=" ),
        CheckResult("MC 5th-pct PF > 0.9", True,      0.95,     0.9         ),
        CheckResult("DSR z-score > 0",     True,       0.5,      0.0         ),
    ]
    return GateResult(verdict=verdict, n_trades=n, checks=checks)


def _edge_pass(outperf: float = 0.20) -> EdgeResult:
    return EdgeResult(
        alpha_pf=1.25,
        random_baseline_pf=1.25 / (1 + outperf),
        random_p_value=0.02,
        outperformance_pct=outperf,
        edge_threshold_pct=0.10,
        passed=outperf >= 0.10,
        n_trades=500,
        n_permutations=10_000,
    )


def _edge_fail() -> EdgeResult:
    return EdgeResult(
        alpha_pf=1.05,
        random_baseline_pf=1.00,
        random_p_value=0.30,
        outperformance_pct=0.05,
        edge_threshold_pct=0.10,
        passed=False,
        n_trades=200,
        n_permutations=10_000,
    )


engine = TRGSDecisionEngine()


# ── BLOCKED ────────────────────────────────────────────────────────────────────

class TestBlocked:
    def test_hard_blocker_overrides_everything(self):
        result = engine.evaluate(
            _gate_result("ROBUST"),
            _edge_pass(),
            TIMESTAMP,
            manual_override=True,
            hard_blockers=["look-ahead test FAIL in LiquidityDetector"],
        )
        assert result.status == ReadinessStatus.BLOCKED

    def test_blocked_even_if_gate_robust_and_override_true(self):
        result = engine.evaluate(
            _gate_result("ROBUST", n=600, dd=0.05),
            _edge_pass(),
            TIMESTAMP,
            manual_override=True,
            hard_blockers=["replay integrity: execution before signal at bar 123"],
        )
        assert result.status == ReadinessStatus.BLOCKED

    def test_blocked_records_blocker_message(self):
        msg = "timestamp mismatch in trade log"
        result = engine.evaluate(_gate_result("ROBUST"), _edge_pass(), TIMESTAMP,
                                 hard_blockers=[msg])
        assert msg in result.blockers


# ── NOT_READY ──────────────────────────────────────────────────────────────────

class TestNotReady:
    def test_fragile_verdict_is_not_ready(self):
        result = engine.evaluate(_gate_result("FRAGILE", n=30), _edge_pass(), TIMESTAMP)
        assert result.status == ReadinessStatus.NOT_READY

    def test_fragile_blocker_message(self):
        result = engine.evaluate(_gate_result("FRAGILE", n=30), _edge_pass(), TIMESTAMP)
        assert any("FRAGILE" in b for b in result.blockers)


# ── READY_FOR_BACKTEST ─────────────────────────────────────────────────────────

class TestReadyForBacktest:
    def test_read_verdict_without_edge_is_backtest_ready(self):
        result = engine.evaluate(_gate_result("READ", n=80), _edge_fail(), TIMESTAMP)
        assert result.status == ReadinessStatus.READY_FOR_BACKTEST

    def test_robust_without_edge_stays_backtest_ready(self):
        result = engine.evaluate(_gate_result("ROBUST", n=600), _edge_fail(), TIMESTAMP)
        assert result.status == ReadinessStatus.READY_FOR_BACKTEST


# ── READY_FOR_PAPER ────────────────────────────────────────────────────────────

class TestReadyForPaper:
    def test_read_verdict_with_edge_is_paper_ready(self):
        result = engine.evaluate(_gate_result("READ", n=80), _edge_pass(), TIMESTAMP)
        assert result.status == ReadinessStatus.READY_FOR_PAPER

    def test_robust_below_shadow_n_is_paper_ready(self):
        # ROBUST but n < 500
        result = engine.evaluate(_gate_result("ROBUST", n=250, dd=0.08), _edge_pass(), TIMESTAMP)
        assert result.status == ReadinessStatus.READY_FOR_PAPER

    def test_robust_above_shadow_dd_is_paper_ready(self):
        # ROBUST, n >= 500, but DD >= 10%
        result = engine.evaluate(_gate_result("ROBUST", n=600, dd=0.12), _edge_pass(), TIMESTAMP)
        assert result.status == ReadinessStatus.READY_FOR_PAPER

    def test_blocker_lists_shadow_reason(self):
        result = engine.evaluate(_gate_result("ROBUST", n=200, dd=0.08), _edge_pass(), TIMESTAMP)
        assert any("500" in b or "shadow" in b.lower() for b in result.blockers)


# ── READY_FOR_SHADOW ───────────────────────────────────────────────────────────

class TestReadyForShadow:
    def test_robust_n500_dd10_no_override_is_shadow(self):
        result = engine.evaluate(
            _gate_result("ROBUST", n=550, dd=0.07), _edge_pass(), TIMESTAMP,
            manual_override=False,
        )
        assert result.status == ReadinessStatus.READY_FOR_SHADOW

    def test_shadow_blocker_lists_override_requirement(self):
        result = engine.evaluate(
            _gate_result("ROBUST", n=550, dd=0.07), _edge_pass(), TIMESTAMP,
        )
        assert any("manual_override" in b or "OWNER" in b for b in result.blockers)

    def test_exact_shadow_n_boundary(self):
        # n = 500 exactly → READY_FOR_SHADOW
        result = engine.evaluate(
            _gate_result("ROBUST", n=500, dd=0.09), _edge_pass(), TIMESTAMP,
        )
        assert result.status == ReadinessStatus.READY_FOR_SHADOW

    def test_one_below_shadow_n_boundary(self):
        # n = 499 → READY_FOR_PAPER
        result = engine.evaluate(
            _gate_result("ROBUST", n=499, dd=0.09), _edge_pass(), TIMESTAMP,
        )
        assert result.status == ReadinessStatus.READY_FOR_PAPER


# ── READY_FOR_LIVE ─────────────────────────────────────────────────────────────

class TestReadyForLive:
    def test_shadow_plus_override_is_live(self):
        result = engine.evaluate(
            _gate_result("ROBUST", n=600, dd=0.07), _edge_pass(), TIMESTAMP,
            manual_override=True,
        )
        assert result.status == ReadinessStatus.READY_FOR_LIVE

    def test_live_records_override_in_promoters(self):
        result = engine.evaluate(
            _gate_result("ROBUST", n=600, dd=0.07), _edge_pass(), TIMESTAMP,
            manual_override=True,
        )
        assert any("manual_override" in p or "OWNER" in p for p in result.promoters)


# ── JSON Report ────────────────────────────────────────────────────────────────

class TestReport:
    def test_json_parseable(self):
        result = engine.evaluate(_gate_result("ROBUST", n=600, dd=0.07), _edge_pass(), TIMESTAMP)
        parsed = json.loads(result.to_json())
        assert parsed["status"] == "READY_FOR_SHADOW"

    def test_json_contains_thresholds(self):
        result = engine.evaluate(_gate_result("READ", n=80), _edge_pass(), TIMESTAMP)
        parsed = json.loads(result.to_json())
        assert "thresholds" in parsed
        assert parsed["thresholds"]["shadow_min_trades"] == 500
        assert parsed["thresholds"]["shadow_max_drawdown"] == pytest.approx(0.10)

    def test_text_report_shows_status(self):
        result = engine.evaluate(_gate_result("READ", n=80), _edge_pass(), TIMESTAMP)
        assert result.status.value in result.report()

    def test_timestamp_preserved(self):
        result = engine.evaluate(_gate_result("ROBUST", n=600, dd=0.07), _edge_pass(), TIMESTAMP)
        parsed = json.loads(result.to_json())
        assert parsed["timestamp_utc"] == TIMESTAMP
