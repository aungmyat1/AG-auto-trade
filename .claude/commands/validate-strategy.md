---
description: Run the full validation workflow on a strategy/alpha (tests + gate + verdict recording)
argument-hint: [alpha-id or trades.csv] [instrument] [n-trials]
---

Use the strategy-validator skill on: $ARGUMENTS

Follow every step of the skill — tests first, honest trial count, net-of-cost gate run via
`scripts/run_gate.py`, verdict recorded in VALIDATION_STATUS.md / GROUND_TRUTH.md /
docs/PROJECT_STATE.md (and research_archive/ if FRAGILE). If no trade series exists for the
target, report NOT TESTED and what data is needed — do not fabricate or approve anything.
