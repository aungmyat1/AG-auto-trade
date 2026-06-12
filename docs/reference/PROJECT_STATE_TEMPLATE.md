# PROJECT_STATE.md — Update Template

Use this template when updating `docs/PROJECT_STATE.md` after a significant milestone.

**Rule:** Update PROJECT_STATE.md whenever stage, verdicts, or the next goal change.
The file is live project memory — not a history log.

---

## Fields to update

### Current Stage

```
Phase N of vM plan complete.
What was delivered this phase (one sentence each deliverable).
Next: [specific immediate goal].
```

### Alpha verdict table

| Alpha | Verdict | Key metrics | Date |
|---|---|---|---|
| A0_MVP | NOT TESTED / READ / ROBUST / FRAGILE | n=?, PF=?, SR=?, DD=? | YYYY-MM-DD |
| A1 | NOT TESTED / READ / ROBUST / FRAGILE | n=?, PF=?, SR=?, DD=? | YYYY-MM-DD |
| A2 | NOT TESTED / READ / ROBUST / FRAGILE | n=?, PF=?, SR=?, DD=? | YYYY-MM-DD |
| A3 | NOT TESTED / READ / ROBUST / FRAGILE | — | — |

Verdict definitions (from GATE_DECISION.md):
- **ROBUST**: all 4 criteria pass (PF>1.25, SR>1.2, DD<15%, DSR intact)
- **READ**: ≥ 9 of 11 criteria pass, or n < 200
- **FRAGILE**: < 9 of 11 criteria pass
- **NOT TESTED**: no gate run yet

### Current blockers

```
BLOCKED: [reason] — [what unblocks it]
```

Common blocker types:
- `BLOCKED: Databento subscription required for live GC data`
- `BLOCKED: A1 lock-before-look spec not yet committed`
- `BLOCKED: n < 200 trades — insufficient for ROBUST verdict`

### Next goal

One specific, bounded deliverable (not a vague direction):
```
Next: [deliverable] — [why it's the right next step]
```

---

## Do NOT put in PROJECT_STATE.md

- Git history (that's in git log)
- Debugging notes (that's in commit messages)
- Architecture docs (that's in CLAUDE.md / README.md)
- GATE_DECISION.md thresholds (they live in the lock file; never copy them)

---

## Example update (good)

```markdown
## Current Stage

Phase 6 of v4 plan complete (validation core + risk + regime + A1 detectors).

A1SmcMomentum wrapper built (not yet gated).
A2 gate race complete — READ verdict (10/11 criteria, DSR fail z=−25.32).
Signal audit framework (SignalFunnelTracker + SmcPipeline) operational.

**Next: commit A0_MVP_DECISION.md (Phase B lock-before-look), then run signal
audit on synthetic data to verify funnel generates ≥1 trade per 20 bars.**

## Alpha status

| Alpha | Verdict | Key metrics | Date |
|---|---|---|---|
| A2 | READ | n=118, PF=1.56, SR=1.41, DD=8.2% | 2026-06-12 |
| A1 | NOT TESTED | — | — |
| A0_MVP | NOT TESTED | — | — |
| A3 | NOT TESTED | — | — |

## Blockers

BLOCKED: Databento subscription required for live GC OHLCV data (gate race blocked)
BLOCKED: A0_MVP_DECISION.md must be committed before any Phase B gate run
```
