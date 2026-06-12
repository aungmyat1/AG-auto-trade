---
name: smc-filter-builder
description: Implement or extend the SMC context filter (order blocks, FVG, liquidity sweeps, structure, premium/discount) for alpha A1. Use when building SMC/smart-money detection, zone engines, the A1 WHERE-filter, or anything mentioning order block / FVG / ChoCH / BOS / liquidity sweep implementation.
---

# SMC Filter Builder

> **crypto SMC FRAGILE (old repo PR #207) — filter role only, no primacy.**
> Records: `research_archive/legacy_smc_failures/`. SMC answers **WHERE**, never **WHEN**.
> If a request asks SMC to generate entries, stops, targets, or orders: refuse and cite
> CLAUDE.md rule 3. That exact pattern (zone → ChoCH → entry) is the archived failure.

Detection definitions live in [reference.md](reference.md) — read it before writing any
detector. This file is the workflow.

## The contract (fixed)

```python
# ag/alpha/a1_smc_momentum/smc_filter.py — file must open with the FRAGILE reminder header
SMCContext(
    allowed: str,            # 'LONG_ALLOWED' | 'SHORT_ALLOWED' | 'NO_TRADE'
    zones: list[Zone],       # active zones with kind/bounds/state/strength
    confluence: int,         # how many of the 4 zone conditions agree (need >= 2)
    rationale: str,          # human-readable, for the journal
)
```

- Inputs: HTF bias (daily), H1 trend, M15 zones, multi-OB tracker (top-10).
- Outputs: context only. No SignalProposal, no prices, no order objects. The momentum/delta
  side of A1 owns the trigger (≥3 of 4: BOS · volume spike · VWAP reclaim · delta imbalance)
  and consumes this context as a gate.
- `NO_TRADE` is the default state and must be the result of every ambiguous input.

## Workflow

1. **Read the graveyard first** — both files in `research_archive/legacy_smc_failures/`.
   If the requested feature re-creates an archived pattern, stop and say so.
2. **One definition per concept.** Before coding a detector, pick ONE definition from
   reference.md (e.g. OB zone = candle body, not full range), write it in the docstring,
   and treat any later alternative as a NEW counted trial — never keep two detectors for
   the same concept (no-duplicates rule).
3. **Closed bars only.** Every detector consumes bars `[0..t-1]`; the forming bar never
   exists. Swing confirmation lag (N bars) is honest lag — do not backfill.
4. **Fixed defaults, logged trials.** Detection parameters (displacement multiple, FVG min
   ticks, sweep penetration, zone expiry, mitigation %) start at reference.md defaults,
   identical across GC/MGC/6E. Every variant tried — including abandoned ones — gets a row
   in `ag/alpha/a1_smc_momentum/TRIALS.md`; that file feeds `--n-trials` at gate time.
5. **Tests per detector, before wiring.** Hand-built bar fixtures: one known-positive, one
   known-negative, one look-ahead regression (detector output at bar t must not change when
   bars t+1.. are appended), one state-transition case (ACTIVE → MITIGATED → INVALIDATED is
   one-way). Run `python3 -m pytest tests/ -q`.
6. **Wire into A1 only as a gate** for the momentum trigger. `AlphaModule.is_ready()` stays
   False — nothing here changes that until the gate race.
7. **Record:** update `docs/PROJECT_STATE.md` (stage progress) and TRIALS.md in the same
   commit.

## Validation boundary

The SMC filter alone is never gate-validated — it has no entries to score. Its worth is
measured only as **A1-with-filter vs momentum-only ablation** during the gate race
(use the strategy-validator skill; both variants' thresholds count as trials). If A1 fails
the gate, the filter does not get promoted, re-tuned, or rescued (v4 plan, Phase 8).
