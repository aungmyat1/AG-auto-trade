---
name: strategy-validator
description: Validate a strategy/alpha against the locked AG gate. Use whenever strategy or alpha code changes, when backtest results appear, before any deployment claim, or when asked to validate/approve a strategy.
---

# Strategy Validator

Never approve anything without evidence. The output of this workflow is a verdict
(ROBUST / FRAGILE / FLOOR-only), not an opinion.

## Steps

1. **Unit tests first.** `python3 -m pytest tests/ -q`. Red suite = stop; fix tests before
   validating anything.

2. **Locate the evidence.** A validation run needs a chronological per-trade R-multiple
   series (CSV with a `pnl_r` column). If the requester has no trade series, the strategy
   is NOT TESTED — say so and stop. Do not validate on synthetic or cherry-picked samples.

3. **Establish the honest trial count.** Ask/derive how many parameter combos, thresholds,
   and variants were tried across the strategy's history — including discarded ones. This is
   `--n-trials` for Deflated Sharpe. When in doubt, round UP.

4. **Run the gate battery:**
   ```bash
   python3 scripts/run_gate.py <trades.csv> --instrument <GC|MGC|6E> \
       --cost-preset <gc|6e> --n-trials <honest count>
   ```
   Exit 0 = ROBUST, exit 1 = anything less. Costs are mandatory — never use
   `--cost-preset zero` for a verdict.

5. **Compare against the locked thresholds** in `ag/validation/lock_before_look/GATE_DECISION.md`.
   The gate code mirrors them; if you ever find a mismatch, that is a critical finding —
   report it, do not "fix" either side silently.

6. **Record the verdict:**
   - Update the alpha's row in `VALIDATION_STATUS.md` (status, n, net PF, verdict, date).
   - Update the alpha table in `GROUND_TRUTH.md`.
   - FRAGILE/FAIL → create `research_archive/<date>_<name>/README.md` with a one-line
     verdict header (what it was, why it died, key numbers) plus a `verdict.json`.
   - Update `docs/PROJECT_STATE.md` (stage, last validation evidence).

7. **Report.** State the verdict, the failing checks (if any), n, net PF, and trial count.
   If FRAGILE: the next step is the archive, NOT parameter tweaking — re-tuning after seeing
   gate results is how the trial count explodes.

## Refusals (hard)

- No verdict without net-of-cost numbers.
- Never suggest relaxing a threshold to let a candidate pass.
- Never re-test an archived FRAGILE strategy unless the owner explicitly orders it with a
  documented reason (and the re-test inflates its trial count).
