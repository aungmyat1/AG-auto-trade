# AG-auto-trade Documentation Index

**Last Updated**: 2026-06-12

## Core Project Documents (in repo)

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/PROJECT_STATE.md` | Live project memory — read first every session | Current |
| `VALIDATION_STATUS.md` | Alpha gate verdicts | Current |
| `ag/validation/lock_before_look/GATE_DECISION.md` | Locked gate thresholds (immutable) | Locked |
| `ag/validation/lock_before_look/A1_SMC_MOMENTUM_DECISION.md` | A1 spec (locked 2026-06-12) | Locked |
| `docs/validation/A2_GATE_RESULT.md` | A2 gate run output | Finalized |

## Reference Documents (planning, not locked)

| Document | Purpose | Status |
|----------|---------|--------|
| `ROADMAP_v1.md` | v1 planning roadmap (partially superseded by v4) | Reference |
| `PROJECT_OVERVIEW.md` | Architecture, principles, constraints | Reference |
| `CURRENT_STATUS_SNAPSHOT_2026-06-12.md` | Snapshot (STALE: A2 now implemented) | Reference |
| `VALIDATION_GATE_SPEC.md` | Gate v2 planning (NOT current locked spec) | Reference |
| `QUICKSTART.md` | Getting started guide | Reference |
| `PHASE1_TECHNICAL_SPEC.md` | Phase 1 requirements (reconciled 2026-06-12) | Reference |
| `PHASE1_RUNBOOK.md` | Week-by-week execution plan (reconciled 2026-06-12) | Reference |
| `SMC_CONCEPT_LIBRARY.md` | SMC concept definitions | Reference |
| `SMC_CONCEPT_VALIDATION_CHECKLIST.md` | Quality gate for new concepts | Reference |
| `SMC_IMPLEMENTATION_SKELETONS_README.md` | Points to actual code in ag/alpha/a1_smc_momentum/ | Reference |
| `DOCS_INDEX.md` | This file | Reference |

## How to Navigate

1. Start with `docs/PROJECT_STATE.md` (in repo root docs/) for current reality
2. Gate is locked in `ag/validation/lock_before_look/GATE_DECISION.md` — do not modify
3. Use `ROADMAP_v1.md` for overall vision; cross-check against PROJECT_STATE.md
4. SMC detector code lives in `ag/alpha/a1_smc_momentum/detectors/` — not research_archive/
5. `research_archive/` contains validated-NEGATIVE results only

## IMPORTANT: Document Conflicts

Several reference documents contain thresholds/state that diverge from the live repo:
- `VALIDATION_GATE_SPEC.md` — uses sharpe ≥ 1.8, DD ≤ 12%, PF ≥ 1.6 (Gate v2 draft, not locked)
- `CURRENT_STATUS_SNAPSHOT_2026-06-12.md` — says A2 not implemented (stale: A2 = READ)
- `QUICKSTART.md` — says 21 tests passing (stale: 173+ as of 2026-06-12)

When in doubt, the repo files always take precedence over documents in this folder.
