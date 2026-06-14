# DISPATCH — A1_WHERE_ONLY funnel diagnosis (measurement only)

**Target:** VPS WORKER (has the cached 5yr GC/6E 1h parquet).
**From:** Cloud MAIN. **Purpose:** empirically confirm/refute the code-level hypothesis that
n=33 is **(b) over-strict AND-gating**, not (a) genuine rarity or (c) a detector bug.
**Committed:** 2026-06-14.

> ⚠️ **DIAGNOSIS ONLY.** Do NOT tune, loosen, or add features. Touch zero detector logic.
> This measures the EXISTING funnel on the ALREADY-CACHED data. It changes nothing.

## What to measure

The `SignalFunnelTracker` (audit tracker) already counts per-stage rejections in
`a1_alpha.propose()`: `NO_SWEEP`, `NO_CHOCH`, `NO_OB_UNMITIGATED`, `NO_FVG`,
`NO_DISPLACEMENT`, and `entries_generated`. Run the existing A1_WHERE_ONLY backtest and dump them.

```bash
python3 - <<'PY'
import pandas as pd
from ag.alpha.a1_smc_momentum.a1_alpha import A1SmcMomentum
from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig

cfg = PipelineConfig(sweep=True, choch=True, ob=True, fvg=True, displacement=True)  # as-built; do NOT change

for sym in ("GC", "6E"):
    df = pd.read_parquet(f"data/cache/{sym}_1h.parquet")
    alpha = A1SmcMomentum(config=cfg)
    lookback = 50
    # (1) cumulative AND-funnel — count bars surviving each sequential gate
    for i in range(lookback, len(df)):
        alpha.propose({"df": df.iloc[i-lookback:i+1]})
    print(f"\n=== {sym}: AND-funnel (audit tracker) ===")
    print(alpha.audit.summary())   # NO_SWEEP / NO_CHOCH / NO_OB / NO_FVG / NO_DISPLACEMENT / entries

    # (2) per-component independent hit-rate — how often does EACH component fire ALONE?
    #     (read-only: run each detector via the pipeline; do not change thresholds)
    from ag.alpha.a1_smc_momentum.pipeline import SmcPipeline
    hits = {"sweep":0,"struct":0,"ob":0,"fvg":0,"displacement":0,"bars":0}
    for i in range(lookback, len(df)):
        r = SmcPipeline(cfg).run(df.iloc[i-lookback:i+1])
        hits["bars"] += 1
        hits["sweep"] += bool(r.sweeps)
        hits["struct"] += bool(r.choch_events or r.bos_events)
        hits["ob"] += bool(r.obs)
        hits["fvg"] += bool(r.fvgs)
        hits["displacement"] += bool(r.displacements)
    print(f"=== {sym}: independent per-component hit-rate ===")
    print({k: (v, round(100*v/max(hits['bars'],1),1)) for k,v in hits.items() if k!='bars'},
          "of", hits["bars"], "bars")
PY
```

## How to read it (classification)

- **(b) over-strict AND-gating** — confirmed if each component fires reasonably often *alone*
  (e.g. sweep, OB, FVG each on 10–40% of bars) but the **AND-intersection** (entries) is ~0.3%.
  The bottleneck is the *conjunction*, not any single stage. → A spec-conformant **≥k-of-n
  confluence** (a NEW alpha, fresh window) might fairly test the edge.
- **(a) genuine rarity** — if even the most permissive component (e.g. sweep) fires on <2% of
  bars, the setups themselves are rare on CME H1 → WHERE-only SMC-as-entry is concluded done.
- **(c) detector bug** — if a component that should fire often reports ~0 hits (e.g. OB never
  fires despite the multi-OB tracker), flag the detector. (Code review already refuted single-OB
  tracking; this is the empirical backstop.)

## Report
Write `docs/validation/A1_FUNNEL_RESULT.md`: the per-stage AND-funnel counts + the independent
per-component hit-rates for GC and 6E, and the one-line classification (a/b/c). Hand back to
Cloud MAIN. **Do not act on it** — the classification drives the owner's build-vs-promote call.

## Constraints
No tuning, no threshold/logic change, no new features. Keys stay on the WORKER. Commit via PR.
