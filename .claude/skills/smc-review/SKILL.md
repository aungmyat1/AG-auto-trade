---
name: smc-review
description: Review SMC/zone-detection code for look-ahead bias, repainting, entry-smuggling, and threshold sprawl. Use when reviewing changes touching ag/alpha/a1_smc_momentum, order-block/FVG/sweep detectors, or any PR labeled SMC.
---

# SMC Code Review

SMC code earns extra scrutiny: it is the one component with a standing FRAGILE verdict
(`research_archive/legacy_smc_failures/`), kept on probation as a filter. Review verdict
is PASS / FAIL per item with file:line evidence.

## 1. Contract integrity (instant FAIL if violated)

- Outputs limited to `LONG_ALLOWED | SHORT_ALLOWED | NO_TRADE` + zone metadata. Grep the
  diff for entry smuggling: `SignalProposal`, `entry`, `stop`, `target`, `order`,
  `propose(` inside SMC filter files — none may originate there.
- No `ChoCH → entry` resurrection: structure labels (BOS/ChoCH) may inform context or one
  trigger vote, never fire a trade alone.
- The FRAGILE reminder header is present at the top of every SMC filter file.
- Default/ambiguous path returns `NO_TRADE` (fail-closed, never fail-open to a direction).

## 2. Look-ahead & repainting

- Detectors read only closed bars; no `iloc[-1]` on a forming bar, no `center=True`
  rolling windows, no `.shift(-`.
- Swing confirmation lag (N bars) respected; zones dated from their confirm bar.
- Zone states one-way (`ACTIVE → MITIGATED → INVALIDATED`); no bound mutation after emit.
- The append-future-bars regression test exists and covers the new detector.

## 3. Single-definition & no-duplicates

- Exactly one detector per concept (one OB definition, one FVG, one sweep). A second
  variant in parallel = FAIL (old repo died of duplicate subsystems).
- Definition in the docstring matches `smc-filter-builder/reference.md`; divergence is
  either a documented new trial or a FAIL.

## 4. Threshold discipline

- Every new/changed parameter has a row in `ag/alpha/a1_smc_momentum/TRIALS.md` (the DSR
  trial ledger). Unlogged tuning = FAIL.
- No per-instrument hand-tuning: GC/MGC/6E share defaults unless a logged, gate-tested
  reason exists. Tick-size scaling is fine; "GC works better with 1.8" is not.
- No magic numbers in code that bypass the declared parameter set.

## 5. Tests & hygiene

- Per-detector fixtures: known-positive, known-negative, look-ahead regression,
  state-transition. `python3 -m pytest tests/ -q` green.
- Bounded memory: multi-OB tracker capped (top-10); no unbounded zone lists.
- Session windows match `ag/config.py`; news-buffer veto intact.
- `ruff check` clean on touched files.

## Output

Findings table (item, PASS/FAIL, evidence) + one-line verdict. Any FAIL in section 1
blocks merge outright; recommend the strategy-validator skill before any claim that a
change "improves" A1 — improvement claims require a gate run, not a diff.
