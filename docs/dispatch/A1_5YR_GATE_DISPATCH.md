# DISPATCH — A1 5-year gate run (GC · MGC · 6E)

> ⚠️ **SUPERSEDED (2026-06-14 spec↔code audit).** `--alpha a1` builds the **WHERE-only**
> alpha (no WHEN), now registered as **A1_WHERE_ONLY** — and it has already been run:
> GC 5yr n=33<50 → **UNSCOREABLE** (`A1_WHERE_ONLY_DECISION.md`). The full-A1 this dispatch
> was written for is **NOT BUILT**. Do not re-run as-is. Next step is the owner decision in
> `PROJECT_STATE.md` (archive A1_WHERE_ONLY → A2, or build full-A1 and gate on a fresh window).
> Steps below are retained for the MGC/6E mechanics only.

**Target:** VPS WORKER (holds the Databento key; the only tier that may pull paid data).
**From:** Cloud MAIN (no keys; cannot pull data or trade — GROUND_TRUTH #5).
**Committed:** 2026-06-14. Read against `ag/validation/lock_before_look/A1_VERDICT_RULE.md` (locked).

A1 is the first real test of the SMC hypothesis on CME gold/euro futures. A1 is currently
**NOT TESTED** — this is its first gate run. Prior is skeptical (A0_MVP FRAGILE; crypto SMC FRAGILE).
A FRAGILE / READ / UNSCOREABLE result is valid and expected-possible. Do not tune to force a pass.

## Preconditions (all met on main before this dispatch)
- `A1_VERDICT_RULE.md` locked (n-bands, per-instrument, trial honesty) — read the output against it.
- `A1_SMC_MOMENTUM_DECISION.md` §9 locked (per-instrument verdicts, ×N cherry-pick deflation).
- Cost presets exist for all three: `CostModel.for_gc()` / `for_mgc()` / `for_6e()`; CLI `--cost-preset {gc,mgc,6e}` wired in both run scripts.
- Backtest uses the full WHERE filter + logs trials (#21). A1 selectivity guard in ROADMAP.

## Run sequence — repeat INDEPENDENTLY for each instrument ∈ {GC, MGC, 6E}

```bash
# 0. deps (WORKER only; key already in .env on this tier)
pip install -e ".[phase1]"

# 1. Pull ~5 years, 1m, then resample to 1h (A1 is an H1 strategy)
python3 - <<'PY'
from ag.data.loader import get_loader
for sym in ("GC", "MGC", "6E"):
    df = get_loader("databento").load(sym, "1m", start="2020-01-01", end="2024-12-31")
    df_1h = df.resample("1h").agg({"open":"first","high":"max","low":"min",
                                   "close":"last","volume":"sum"}).dropna()
    df_1h.to_parquet(f"data/cache/{sym}_1h.parquet")
    print(sym, "1h bars:", len(df_1h))
PY

# 2. Per instrument: log the A1 trial FIRST, then backtest with the matching cost preset.
#    Adding years/instruments for the SAME filter is NOT a new trial (A1_VERDICT_RULE §5).
#    --n-trials = honest count from trial_log (floor 14). Do NOT under-report.
for SYM in GC MGC 6E; do
  CP=$(echo "$SYM" | tr 'A-Z' 'a-z')                 # GC->gc, MGC->mgc, 6E->6e
  python3 scripts/run_alpha_backtest.py --alpha a1 \
      --data data/cache/${SYM}_1h.parquet \
      --instrument "$SYM" --cost-preset "$CP" \
      --out results/a1_${SYM}_trades.csv
  python3 scripts/run_gate.py results/a1_${SYM}_trades.csv \
      --instrument "$SYM" --cost-preset "$CP" --n-trials <honest count from trial_log>
done
```

## Read each result against A1_VERDICT_RULE.md
- **n < 50 → UNSCOREABLE** (add data/years — NEVER loosen the filter). Low n is the filter working.
- **50 ≤ n < 200 → READ-floor only** (not a capital verdict).
- **n ≥ 200 → score the full locked battery** (net PF>1.25, WR>45%, Sharpe>1.2, MaxDD<15%,
  CPCV med PF>1, WF≥60%, MC p5 PF>0.9, DSR z>0) + MARGINAL (beat unfiltered baseline OOS).

## Report (mandatory)
Write `docs/validation/A1_GATE_RESULT.md` with **all three** instrument verdicts (pass or fail —
no cherry-picking), each with: n (IS/OOS), net PF, the full battery line, realized `--n-trials`,
and the band (UNSCOREABLE / READ / ROBUST / FRAGILE). Then the headline:
- **"A1 ROBUST"** only if ≥1 instrument is ROBUST on its own n≥200 OOS.
- **If no instrument clears n≥200 at 5 years** → *"A1 edge too rare to validate on available data"*
  → archive A1 (`research_archive/a1/`, do-not-tune header) → **promote A2 per ROADMAP Rule 2**.

## Hard constraints
- Keys stay on the WORKER. Net-of-cost is mandatory (use the per-instrument preset) — a PF without
  it is not a result (CLAUDE.md #6).
- Do NOT modify `GATE_DECISION.md` or relax any threshold/filter. The live-trading flag stays OFF —
  it is an owner-only manual flip after a ROBUST verdict + 30-day dry-run; never the agent.
- Extending years = more data, not a new trial. Only a filter change increments `--n-trials`.
- Commit results via PR; keep main green. Hand the three verdicts back to Cloud MAIN to record.
