# A1_WHERE_ONLY — GATE DECISION (lock for what is ACTUALLY built)
# Committed 2026-06-14 to reconcile a spec↔code drift found by the three-layer audit.
# This alpha is NOT the locked full-A1 (A1_SMC_MOMENTUM_DECISION.md §1). It is the
# WHERE-only subset that was actually implemented and run under the "A1" label.

> ⚠️ **HONESTY HEADER.** This is the archived **sweep + ChoCH→entry** pattern
> (CLAUDE.md rule 3: ChoCH/BOS is WHERE context, not a WHEN trigger). It has already
> returned FRAGILE twice — crypto-SMC H1 and A0_MVP. **FRAGILE / UNSCOREABLE is the
> expected verdict.** It is pre-registered under its own ID so that full-A1's §1 spec
> stays clean for an honest future build. Do not tune it to rescue a verdict.

---

## §0 — Why this file exists (the drift)

The locked full-A1 spec (`A1_SMC_MOMENTUM_DECISION.md §1`) requires **≥3-of-4 WHERE
confluence {OB, Volume, BOS, Fib 61.8–78.6%} + ≥2-of-3 WHEN momentum {engulf/pin, RSI
divergence, EMA8 slope}**. The implemented alpha (`_build_alpha("a1")` →
`PipelineConfig(sweep, choch, ob, fvg, displacement)`; `a1_alpha.py::propose`) is:

- **WHEN trigger: ABSENT** — no MT1/MT2/MT3 in `propose()` (only in its docstring).
- **WHERE: sequential AND-gates, not ≥3-of-4 confluence** — sweep AND struct-break AND
  (ob) AND (fvg) AND (displacement). **Fib (Z4) not implemented; FVG + sweep substituted.**

So what ran as "A1" is this WHERE-only alpha. It is gated here under its own ID.

## §1 — Alpha definition (locked to the built code)

Entry fires when ALL enabled components are present in the closed-bar window:

1. **Liquidity sweep** present (`LiquidityDetector`) — required.
2. **Structure break** ChoCH or BOS (`BosChochDetector`) — required.
3. **Order block** retest (`OrderBlockDetector`) — enabled.
4. **Fair value gap** present (`FairValueGapDetector`) — enabled.
5. **Displacement** candle (`DisplacementDetector`) — enabled.

No momentum WHEN gate. No Fib zone. No ≥k-of-n confluence — strict AND.

## §2 — Pre-registered parameters (the orphans, now logged)

These were in code but absent from any decision doc until now:

| Param | Value | Source (file:line) |
|---|---|---|
| `swing_lookback` (sweep + ChoCH) | 5 | `pipeline.py:57` |
| `atr_window` (all detectors) | 14 | `pipeline.py:58` |
| `fvg_min_size_atr` | 0.5 | `pipeline.py:60` |
| OB `displacement_atr_mult` | detector default 1.5 | `pipeline.py:105` |
| liquidity `cluster_atr_mult` | detector default 0.3 | `liquidity.py` |
| displacement `atr_mult` | detector default 1.8 | `displacement.py` |
| stop / target | 0.5% / 1.0% | backtest harness |

## §2b — IS/OOS split (locked before gate run)

Chronological 60/40 split, identical for both instruments:

```
IS period:  2020-01-02 → 2022-12-30  (3 years)
OOS period: 2023-01-02 → 2024-12-30  (2 years)
IS_CUTOFF_DATE = 2022-12-30
```

CPCV, purged WF, and MC run on OOS only. IS bars may not be examined for verdict purposes
after this line is committed.

## §3 — Trial-count floor (recomputed; show the arithmetic)

```
14   base (inherited from A1 §5 — conservative; some of the 14 are WHEN DoF that
     over-count for a WHERE-only alpha, which is the safe direction for DSR)
+ 6  previously-unlogged orphan DoF (the six params in §2 above)
= 20  →  n_trials floor for A1_WHERE_ONLY
```
`--n-trials = max(realized configs, 20)`. trial_log.jsonl realized: A1×2, A0_MVP×1.
Governing n_trials = max(2, 20) = **20**. Under-reporting is self-deception (CLAUDE.md §7).

## §4 — Verdict bands (identical to GATE_DECISION.md; read via A1_VERDICT_RULE.md)

n<50 → UNSCOREABLE · 50≤n<200 → READ-floor · n≥200 → full locked battery
(net PF>1.25, WR>45%, Sharpe>1.2, MaxDD<15%, CPCV med PF>1, WF≥60%, MC p5 PF>0.9, DSR z>0).
Per-instrument, separate, all-three reported. No threshold is relaxed here.

## §5 — Result on hand (2026-06-14, GC 1h 2020–2024)

50 signals → **33 risk-approved → n=33 < 50 → UNSCOREABLE.** WR 66.7%, mean R +0.059
(promising quality, but the gate cannot run on n<50). 6E run = artifact (3 approved; risk
engine state-locked from 2020 COVID volatility — not a valid count). Edge is too **rare**
to validate on available CME H1 data — a frequency limit, not a quality failure.

## §6 — Disposition

Per ROADMAP Rule 2 and A1_VERDICT_RULE §4: if no instrument clears n≥200 even at 5 years,
archive A1_WHERE_ONLY (`research_archive/`, do-not-tune header) and promote A2. Full-A1
(WHERE+WHEN) remains SPEC LOCKED, **NOT BUILT** — building it honestly (and gating on an
unseen window) is a separate, future decision; it must NOT be wired then gated on the
already-seen 2020–2024 data (that would launder seen data — IS/OOS compromised).
