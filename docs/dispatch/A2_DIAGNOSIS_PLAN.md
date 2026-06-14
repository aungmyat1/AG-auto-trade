# PLAN (PARKED) — A2 overfitting diagnosis

> 🅿️ **PARKED — DO NOT EXECUTE.** This becomes live ONLY if the funnel diagnosis
> (`A1_FUNNEL_DIAGNOSIS.md`) concludes WHERE-only SMC-as-entry is done AND the owner elects to
> promote A2 (ROADMAP Rule 2). Until then this is a scoped, ready-to-run plan, not a task.
> **Committed:** 2026-06-14.

## Why A2 needs a diagnosis before it carries the race

A2 (master-trader copy) gated **READ (OPTIMISTIC)**: per-metric edge looks strong
(net PF 3.745, Sharpe 6.34, WR…), but **Deflated Sharpe z = −25.32** — it does not survive
multiple-testing correction. A z that far negative on a PF that high is a classic overfit /
methodology-artifact signature. Before A2 can be trusted as the fallback, three code/methodology
suspects must be ruled out. All are diagnosis-only.

## Suspect 1 — trial-count honesty (is n_trials for A2 honest?)
- Read `A2_MASTER_TRADER_DECISION.md` §trial-count and `A2_GATE_RESULT.md`; reconcile the
  declared n_trials against `trial_log.jsonl` realized entries.
- A DSR z this negative can simply mean a high n_trials (which is honest). Confirm the gate used
  the honest count. **If n_trials was inflated correctly, the READ verdict is sound** and z=−25.32
  is the gate working — not a bug. Establish this first; it may end the diagnosis.

## Suspect 2 — look-ahead in the copy-trade replay
- Read `ag/alpha/a2_master_trader/replay.py` + `a2.py`. Does the replay use ANY post-signal
  information to construct a trade? Specifically: entry priced at/after the signal bar (not the
  bar's own close known only later), exits not peeking at future bars, no use of the trade's
  realized outcome to filter which trades are included.
- Evidence with file:line. A look-ahead here would *inflate* PF (explaining 3.745) while DSR still
  flags it — consistent with the observed split.

## Suspect 3 — survivorship in the SignalStart source
- The 4,437-trade source: is it a winners-only / currently-listed selection? `A2_DATA_SCOPE.md`
  already flags the "OPTIMISTIC" survivorship qualifier (delisted traders excluded).
- Quantify: would including delisted/failed traders plausibly move the verdict? A survivorship-
  selected single trader (UID 279689) with PF 3.745 is exactly what survivorship bias produces.

## Output (when un-parked)
`docs/validation/A2_DIAGNOSIS_RESULT.md`: per-suspect finding (cited), and a classification —
is A2's READ **sound** (honest trials + no look-ahead + survivorship-qualified-but-real), or is
the apparent edge a **methodology artifact** (look-ahead / survivorship)? This decides whether A2
can carry the race or whether the futures-SMC line is concluded (Rule 2 → "no edge" valid result).

## Constraints (when un-parked)
Diagnosis only — no tuning, no re-gating to flatter A2, no GATE_DECISION change. Keys stay off
Cloud MAIN.
