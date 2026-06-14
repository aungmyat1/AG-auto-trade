# A0_MVP — FRAGILE

**Verdict:** FRAGILE — below READ floor, do not tune, do not redeploy.
**Closed:** 2026-06-14
**Purpose:** Pipeline smoke test only. Not a test of the A1 hypothesis.

---

## Result

| Metric | Value | Floor | Pass? |
|---|---|---|---|
| Bars processed | 31,284 | — | — |
| Signals generated | 3,533 | — | — |
| Risk-approved trades | **38** | **≥ 50** | ❌ BELOW FLOOR |
| Win rate | 47.4% | > 45% | ✅ |
| Mean R | −0.003 | — | — |
| Gate run | SKIPPED | n < 50 | — |

**Data:** GC continuous (GC.c.0), GLBX.MDP3, 1m bars, 2022-01-03 → 2024-12-30
**Config:** `PipelineConfig(sweep=True, choch=True, ob=False, fvg=False, displacement=False)`
**Trial count:** 1 (logged in trial_log.py + TRIALS.md)

---

## Why it failed

Sweep + ChoCH → entry is the previously archived `SMC_H1_FRAGILE` pattern
(see `research_archive/legacy_smc_failures/`). ChoCH is a WHERE signal, not a
WHEN signal. Using it as an entry trigger violates the CLAUDE.md §3 contract
(SMC answers WHERE, never WHEN).

Secondary cause: the G3 risk-engine cooldown (1h after 3 consecutive losses)
blocked 99% of the 3,533 signals. Signal rate of 11% (1 in 9 bars) is far too
high for a 1m strategy — this is consistent with sweep+choch firing on noise.

---

## What this proves

- Pipeline is end-to-end functional: data → alpha.propose() → RiskEngine → trade CSV.
- The Databento loader fix (`stype_in="continuous"`) works correctly.
- A1 must reduce signal rate to ~1–2% via the full WHERE filter (OB + FVG + displacement).

## What this does NOT prove

- Nothing about A1. A0_MVP is a plumbing check, not a hypothesis test.

## Decision

Do NOT tune A0_MVP to fix the trade count. The right response is A1 — the full
WHERE filter. Archive this and proceed.
