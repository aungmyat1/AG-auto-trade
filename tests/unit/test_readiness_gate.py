"""Tests for the Trading Readiness Gate System (TRGS).

Covers the fail-closed decision logic, each composing validator, and the
end-to-end property that the gate currently BLOCKS — partly because the replay
validator catches the live LF-1 liquidity look-ahead.
"""
from __future__ import annotations

import types

from ag.readiness import (
    CheckStatus,
    ReadinessGate,
    ReadinessState,
    ValidatorResult,
    backtest_validator,
    edge_validator,
    evaluate_readiness,
    infra_validator,
    replay_validator,
    risk_validator,
    system_health_validator,
)

from tests.replay._smc_cases import DETECT_FNS, make_structured_ohlcv


def _r(name, status, **ev):
    return ValidatorResult(name, status, "", ev)


PASS = CheckStatus.PASS
FAIL = CheckStatus.FAIL
NA = CheckStatus.NOT_AVAILABLE
NR = CheckStatus.NOT_RUN


# ── decision engine: fail-closed + ladder ─────────────────────────────────────

class TestDecisionEngine:
    def _all_required_pass(self):
        return [_r("backtest", PASS), _r("replay", PASS), _r("risk", PASS), _r("edge", PASS)]

    def test_empty_is_not_ready(self):
        rep = ReadinessGate().evaluate([])
        assert rep.state in (ReadinessState.NOT_READY, ReadinessState.BLOCKED)
        assert rep.can_trade_live is False

    def test_any_fail_blocks(self):
        results = self._all_required_pass()
        results[1] = _r("replay", FAIL)  # look-ahead
        rep = ReadinessGate().evaluate(results)
        assert rep.state == ReadinessState.BLOCKED
        assert any("replay" in r for r in rep.reasons)

    def test_harness_verified_but_no_verdict_is_ready_for_backtest(self):
        results = [_r("backtest", NR), _r("replay", PASS), _r("risk", PASS), _r("edge", NR)]
        rep = ReadinessGate().evaluate(results)
        assert rep.state == ReadinessState.READY_FOR_BACKTEST

    def test_all_pass_no_execution_is_paper_only(self):
        results = self._all_required_pass() + [
            system_health_validator(), infra_validator()
        ]
        rep = ReadinessGate().evaluate(results, manual_override=True)
        assert rep.state == ReadinessState.READY_FOR_PAPER  # execution NOT_AVAILABLE caps it

    def test_kill_switch_blocks_live_without_override(self):
        results = self._all_required_pass() + [_r("system_health", PASS), _r("infra", PASS)]
        rep = ReadinessGate().evaluate(results, manual_override=False)
        assert rep.state == ReadinessState.READY_FOR_SHADOW
        assert rep.can_trade_live is False

    def test_live_requires_everything_plus_override(self):
        results = self._all_required_pass() + [_r("system_health", PASS), _r("infra", PASS)]
        rep = ReadinessGate().evaluate(results, manual_override=True)
        assert rep.state == ReadinessState.READY_FOR_LIVE
        assert rep.can_trade_live is True

    def test_report_serializes(self):
        rep = ReadinessGate().evaluate(self._all_required_pass())
        d = rep.to_dict()
        assert d["state"] and "validators" in d
        assert rep.to_json().startswith("{")


# ── individual validators ─────────────────────────────────────────────────────

class TestValidators:
    def test_risk_validator_passes_on_locked_engine(self):
        # All six guards must fire on the locked limits.
        res = risk_validator()
        assert res.status == PASS, res.detail
        assert res.evidence["G1_daily"] and res.evidence["G5_leverage"]

    def test_backtest_validator_rejects_non_robust(self):
        read = types.SimpleNamespace(verdict="READ", n_trades=325)
        assert backtest_validator(read).status == FAIL
        assert backtest_validator(None).status == NR
        robust = types.SimpleNamespace(verdict="ROBUST", n_trades=300)
        assert backtest_validator(robust).status == PASS

    def test_system_health_and_infra_not_available(self):
        assert system_health_validator().status == NA
        assert infra_validator().status == NA

    def test_edge_validator(self):
        # alpha 0.30R vs baseline 0.10R → beats by >10%
        alpha = [0.3] * 100
        base = [0.1] * 100
        assert edge_validator(alpha, base).status == PASS
        # alpha barely above baseline → FAIL the 10% margin
        assert edge_validator([0.10] * 100, [0.099] * 100).status == FAIL
        # negative alpha → FAIL
        assert edge_validator([-0.1] * 100, [0.0] * 100).status == FAIL
        assert edge_validator(None, base).status == NR


# ── replay validator is clean now that LF-1 is fixed ──────────────────────────

class TestReplayValidatorClean:
    def test_replay_validator_passes_on_live_smc_detectors(self):
        df = make_structured_ohlcv()
        res = replay_validator(DETECT_FNS, df)
        # LF-1 fixed → all five detectors are look-ahead- and repaint-clean.
        assert res.status == PASS, res.detail


# ── end-to-end: firewall awaits a verdict (no longer blocked on LF-1) ──────────

class TestEndToEndAwaitsVerdict:
    def test_evaluate_readiness_is_ready_for_backtest(self):
        df = make_structured_ohlcv()
        rep = evaluate_readiness(detect_fns=DETECT_FNS, df=df, manual_override=True)
        # Harness verified (replay clean + risk guards fire) but no ROBUST verdict
        # and no execution layer → READY_FOR_BACKTEST. Never live.
        assert rep.state == ReadinessState.READY_FOR_BACKTEST
        assert rep.can_trade_live is False
