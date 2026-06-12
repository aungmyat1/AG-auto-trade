"""
A4: Lock-before-look consistency test.

Asserts that:
1. ValidationGate class constants match ag/config.py GATE_* constants.
2. GATE_DECISION.md mentions each threshold value (catch copy-paste drift).
3. gate.py thresholds have not been relaxed below the locked values.

If this test fails, either config.py or gate.py was edited after locking.
Neither should be tuned. "No alpha passes" is a valid result.
"""
from __future__ import annotations

import pathlib


from ag.validation.gate import ValidationGate
import ag.config as cfg


GATE_DECISION_MD = (
    pathlib.Path(__file__).parent.parent.parent
    / "ag/validation/lock_before_look/GATE_DECISION.md"
)


def _gate_decision_text() -> str:
    return GATE_DECISION_MD.read_text()


class TestConfigGateAlignment:
    """Gate constants in config.py must match ValidationGate class attributes."""

    def test_read_n(self):
        assert cfg.GATE_READ_N == ValidationGate.READ_N

    def test_read_pf_gross(self):
        assert cfg.GATE_READ_PF_GROSS == ValidationGate.READ_PF_GROSS

    def test_robust_n(self):
        assert cfg.GATE_ROBUST_N == ValidationGate.ROBUST_N

    def test_robust_pf_net(self):
        assert cfg.GATE_ROBUST_PF_NET == ValidationGate.ROBUST_PF_NET

    def test_robust_win_rate(self):
        assert cfg.GATE_ROBUST_WIN_RATE == ValidationGate.ROBUST_WIN_RATE

    def test_robust_sharpe(self):
        assert cfg.GATE_ROBUST_SHARPE == ValidationGate.ROBUST_SHARPE

    def test_robust_max_dd(self):
        assert cfg.GATE_ROBUST_MAX_DD == ValidationGate.ROBUST_MAX_DD

    def test_robust_cpcv_median_pf(self):
        assert cfg.GATE_ROBUST_CPCV_MEDIAN_PF == ValidationGate.ROBUST_CPCV_MEDIAN_PF

    def test_robust_wf_pass_pct(self):
        assert cfg.GATE_ROBUST_WF_PASS_PCT == ValidationGate.ROBUST_WF_PASS_PCT

    def test_robust_mc_p5_pf(self):
        assert cfg.GATE_ROBUST_MC_P5_PF == ValidationGate.ROBUST_MC_P5_PF

    def test_robust_dsr_z(self):
        assert cfg.GATE_ROBUST_DSR_Z == ValidationGate.ROBUST_DSR_Z


class TestGateDecisionMdPresent:
    """GATE_DECISION.md must exist and be non-empty."""

    def test_file_exists(self):
        assert GATE_DECISION_MD.exists(), (
            f"GATE_DECISION.md missing at {GATE_DECISION_MD}"
        )

    def test_file_non_empty(self):
        text = _gate_decision_text()
        assert len(text) > 100

    def test_locked_marker_present(self):
        text = _gate_decision_text()
        assert "Locked:" in text or "PRE-REGISTERED" in text


class TestGateThresholdsNotRelaxed:
    """Gate thresholds must not have been relaxed below locked values."""

    # These are the locked floor values from GATE_DECISION.md (2026-06-12).
    # Tightening is allowed; loosening is not.
    LOCKED_FLOORS = {
        "READ_N": 50,
        "READ_PF_GROSS": 1.0,
        "ROBUST_N": 200,
        "ROBUST_PF_NET": 1.25,
        "ROBUST_WIN_RATE": 0.45,
        "ROBUST_SHARPE": 1.2,
        "ROBUST_MAX_DD": 0.15,       # upper bound — must not INCREASE
        "ROBUST_CPCV_MEDIAN_PF": 1.0,
        "ROBUST_WF_PASS_PCT": 0.60,
        "ROBUST_MC_P5_PF": 0.9,
        "ROBUST_DSR_Z": 0.0,
    }

    def test_min_thresholds_not_lowered(self):
        gate = ValidationGate
        # Lower-bound checks (threshold must be >= locked floor)
        assert gate.READ_N >= self.LOCKED_FLOORS["READ_N"]
        assert gate.READ_PF_GROSS >= self.LOCKED_FLOORS["READ_PF_GROSS"]
        assert gate.ROBUST_N >= self.LOCKED_FLOORS["ROBUST_N"]
        assert gate.ROBUST_PF_NET >= self.LOCKED_FLOORS["ROBUST_PF_NET"]
        assert gate.ROBUST_WIN_RATE >= self.LOCKED_FLOORS["ROBUST_WIN_RATE"]
        assert gate.ROBUST_SHARPE >= self.LOCKED_FLOORS["ROBUST_SHARPE"]
        assert gate.ROBUST_CPCV_MEDIAN_PF >= self.LOCKED_FLOORS["ROBUST_CPCV_MEDIAN_PF"]
        assert gate.ROBUST_WF_PASS_PCT >= self.LOCKED_FLOORS["ROBUST_WF_PASS_PCT"]
        assert gate.ROBUST_MC_P5_PF >= self.LOCKED_FLOORS["ROBUST_MC_P5_PF"]
        assert gate.ROBUST_DSR_Z >= self.LOCKED_FLOORS["ROBUST_DSR_Z"]

    def test_max_drawdown_not_raised(self):
        # Max DD is an upper bound — must NOT be increased (that would relax it)
        assert ValidationGate.ROBUST_MAX_DD <= self.LOCKED_FLOORS["ROBUST_MAX_DD"]


class TestGateDecisionMdThresholds:
    """Key threshold values must appear in GATE_DECISION.md."""

    def test_robust_n_in_doc(self):
        assert "200" in _gate_decision_text()

    def test_robust_pf_in_doc(self):
        assert "1.25" in _gate_decision_text()

    def test_robust_sharpe_in_doc(self):
        assert "1.2" in _gate_decision_text()

    def test_robust_max_dd_in_doc(self):
        text = _gate_decision_text()
        assert "15%" in text or "0.15" in text

    def test_cpcv_in_doc(self):
        assert "CPCV" in _gate_decision_text()

    def test_dsr_in_doc(self):
        text = _gate_decision_text()
        assert "Deflated Sharpe" in text or "DSR" in text
