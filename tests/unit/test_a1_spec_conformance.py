"""Spec <-> code conformance guard for the A1 family.

The audit (2026-06-14) found the implemented "A1" is WHERE-only (no WHEN momentum
trigger), not the locked full-A1 spec. These tests pin that reconciliation so the
drift cannot recur silently: full-A1's spec declares a WHEN gate, the built pipeline
has none, and the built thing is registered under its own A1_WHERE_ONLY id.
"""
from __future__ import annotations

import dataclasses
import pathlib

from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig

LOCK = pathlib.Path("ag/validation/lock_before_look")


def test_full_a1_spec_declares_a_WHEN_trigger():
    spec = (LOCK / "A1_SMC_MOMENTUM_DECISION.md").read_text()
    # full-A1 requires a >=2-of-3 momentum WHEN gate (MT1/MT2/MT3).
    assert "MT1" in spec and "MT2" in spec and "MT3" in spec
    assert "2-of-3" in spec or "≥2-of-3" in spec


def test_built_pipeline_has_NO_when_gate():
    # The implemented config is WHERE-only — no momentum/WHEN field exists.
    fields = {f.name for f in dataclasses.fields(PipelineConfig)}
    forbidden = {"when", "momentum", "mt1", "mt2", "mt3", "rsi", "ema_slope"}
    assert not (fields & forbidden), (
        f"PipelineConfig grew a WHEN-like field {fields & forbidden}; if full-A1's "
        "WHEN trigger was implemented, update A1's decision doc + verdict label and "
        "stop gating it under A1_WHERE_ONLY."
    )
    # WHERE components are the ones actually built.
    assert {"sweep", "choch", "ob", "fvg", "displacement"} <= fields


def test_where_only_alpha_is_registered_under_its_own_id():
    # What was run as "A1" must be pre-registered as WHERE-only with the honesty header,
    # not passed off as the full-A1 spec.
    p = LOCK / "A1_WHERE_ONLY_DECISION.md"
    assert p.exists(), "A1_WHERE_ONLY_DECISION.md missing — the built alpha is unregistered"
    text = p.read_text()
    assert "HONESTY HEADER" in text
    assert "WHEN trigger: ABSENT" in text
