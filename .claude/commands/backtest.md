---
description: Run the net-of-cost gate battery on a trades CSV
argument-hint: <trades.csv> <GC|MGC|6E> <n-trials>
---

Run the gate battery on: $ARGUMENTS

```bash
python3 scripts/run_gate.py <csv> --instrument <inst> --cost-preset <gc|6e> --n-trials <n>
```

Rules:
- The CSV needs a chronological `pnl_r` column (per-trade R-multiples).
- Cost preset must match the instrument (`gc` for GC/MGC, `6e` for 6E). Never `zero` for a verdict.
- `--n-trials` is the HONEST count of all variants/thresholds ever tried for this strategy —
  if the user didn't supply one, ask or derive it; round up.
- Print the full gate report and state the verdict plainly. Exit 1 means NOT ROBUST — report
  exactly which checks failed against `ag/validation/lock_before_look/GATE_DECISION.md`.
- A FRAGILE result is a result: next stop is research_archive/, not parameter tweaking.
