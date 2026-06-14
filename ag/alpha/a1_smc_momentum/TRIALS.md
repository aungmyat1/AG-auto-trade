# A1 SMC Momentum — Trial Registry

**Canonical trial counter:** `ag/validation/trial_log.py` (TrialRegistry) is the
authoritative source for `--n-trials` at gate time. This file documents the *declared
parameter baseline* so any deviation is immediately visible as a new trial.

Every parameter change, filter toggle, or threshold adjustment **must** be logged in
`trial_log.py` BEFORE the run. `--n-trials` = `TrialRegistry().count("A0_MVP")` (or
`"A1"` etc.) at the moment the gate is invoked. Under-counting = self-deception (§7).

---

## Declared baseline parameters (A0_MVP — trial 1)

| Parameter | Value | Source |
|---|---|---|
| `PipelineConfig.sweep` | `True` | A0_MVP_DECISION.md |
| `PipelineConfig.choch` | `True` | A0_MVP_DECISION.md |
| `PipelineConfig.ob` | `False` | A0_MVP_DECISION.md |
| `PipelineConfig.fvg` | `False` | A0_MVP_DECISION.md |
| `PipelineConfig.displacement` | `False` | A0_MVP_DECISION.md |
| `swing_lookback` | `5` | LiquidityDetector / BosChochDetector default |
| `stop_distance_pct` | `0.5` | A0_MVP_DECISION.md |
| `target_distance_pct` | `1.0` | A0_MVP_DECISION.md (R:R = 2.0) |
| `atr_window` | `14` | All detectors default |

**Trial 1 registered:** `TrialRegistry().log("A0_MVP", "base: sweep+choch, swing_lookback=5, stop=0.5%, target=1.0%")`

---

## Declared baseline parameters (A1 — pending)

A1 spec is locked in `ag/validation/lock_before_look/A1_SMC_MOMENTUM_DECISION.md`.
Parameters will be logged here and in `trial_log.py` before the first A1 gate run.

---

## Rules

1. Each new entry here = one new trial = `--n-trials` increments by 1.
2. Never delete or edit past entries — this is an append-only ledger (mirrors `trial_log.py`).
3. Gate time: `--n-trials <TrialRegistry().count("A0_MVP")>` — no manual counting.
