# A1 VERDICT RULE — how to read the A1 5-year gate output
# LOCK-BEFORE-LOOK. Committed BEFORE the VPS run, before any A1 numbers exist.
# Operationalises §9 of A1_SMC_MOMENTUM_DECISION.md; thresholds are GATE_DECISION.md (immutable).
# Date locked: 2026-06-14

This file is the binding decision procedure for reading the A1 gate output. Read the result
against THIS — do not decide pass/fail after seeing the numbers.

---

## 1 — Score bands by trade count (n = net OOS trades, per instrument)

| n (OOS, net) | Outcome | Meaning |
|---|---|---|
| **n < 50** | **UNSCOREABLE** | The gate cannot run. Not a verdict. Add data / years / instruments. **NEVER loosen the filter** to manufacture trades. |
| **50 ≤ n < 200** | **READ-floor only** | Data exists, edge unproven. **Not a capital verdict** — label it READ, never imply ROBUST. |
| **n ≥ 200** | **SCOREABLE** | Run the full locked battery (§3) and assign ROBUST or FRAGILE. |

## 2 — Per-instrument, SEPARATE verdicts

GC, MGC, 6E are scored **independently** — each its own trade series, IS/OOS split, cost model
(`CostModel.for_gc()` / `for_mgc()` / `for_6e()`), realized trial count, and verdict.

- A **thin** instrument (UNSCOREABLE / READ) does **not** sink a passing one.
- A **passing** instrument does **not** rescue a thin one.
- **No cherry-picking** the best of three. **All three verdicts are reported**, pass or fail, in
  `A1_GATE_RESULT.md`. (Reporting only the winner would multiply that claim's DSR trial count by
  the number of instruments searched — see §9 of A1_SMC_MOMENTUM_DECISION.md. Reporting all
  pre-empts the penalty.)

## 3 — ROBUST battery (only at n ≥ 200, net of cost) — identical to GATE_DECISION.md

ROBUST requires **all** of:

```
net PF > 1.25     win rate > 45%      Sharpe > 1.2       max DD < 15%
CPCV median PF > 1.0      purged-WF folds PF>1 ≥ 60%      MC 5th-pct PF > 0.9
Deflated Sharpe z > 0   (trial-count-aware; n_trials = honest count, floor 14)
```

Any check fails ⇒ **FRAGILE**. A MARGINAL check also applies: A1 net OOS PF must beat the
unfiltered-baseline OOS PF on the same window (§6 of A1_SMC_MOMENTUM_DECISION.md). Passing the
LEVEL battery but failing MARGINAL = **READ**, not ROBUST.

## 4 — Headline + fallback

- **"A1 ROBUST"** may be claimed only when **≥ 1 instrument is ROBUST on its own n ≥ 200 OOS**
  net trades passing the full battery.
- **If no instrument clears n ≥ 200 even at 5 years** → verdict: *"A1 edge too rare to validate
  on available data."* → archive A1 to `research_archive/a1/` with a do-not-tune header →
  **promote A2 per ROADMAP Rule 2** (A2 is TESTED/READ and available; race it / build A3).
- FRAGILE instruments → `research_archive/` with header; never re-promoted, never re-tuned.

## 5 — Trial-count honesty (the rule that keeps DSR honest)

- **Extending the date range / adding years is NOT a new trial** — same filter, more data. It
  does **not** increment `--n-trials`. (Adding data to lift n is the sanctioned fix for a thin
  instrument; it carries no DSR penalty.)
- **Only a filter/parameter change is a new trial** (+1 each), per §5 of A1_SMC_MOMENTUM_DECISION.md
  (floor 14). Adding instruments for the *same* filter is reported (§2), not a free pass.
- `--n-trials` at gate time = the honest count logged in `TRIALS.md` / `trial_log`. Under-reporting
  is self-deception (CLAUDE.md §7).

---

This rule does not relax any threshold. n-bands route to the locked battery; they do not replace
it. UNSCOREABLE and READ are honest labels for "not enough evidence," not softer pass criteria.
