# A1-WHERE-ONLY — LOCKED GATE SPEC
# Committed 2026-06-14 BEFORE the IS/OOS gate run.
# Describes the code ACTUALLY BUILT: A1SmcMomentum with
#   PipelineConfig(sweep=True, choch=True, ob=True, fvg=True, displacement=True)
# The aspirational full-A1 (WHERE+WHEN, Z1–Z4, MT1–MT3) lives in
#   A1_SMC_MOMENTUM_DECISION.md §1 — NOT BUILT, untouched.

---

## §0 — WHAT THIS ALPHA IS (AND IS NOT)

**A1_WHERE_ONLY** is a pure context-filter entry: a liquidity sweep followed by a
structure break, validated by an Order Block, a Fair Value Gap, and a displacement candle.
There is no WHEN momentum gate — entry fires on WHERE signals alone.

This differs materially from the locked A1 spec (A1_SMC_MOMENTUM_DECISION.md §1), which
requires both WHERE (Z1–Z4, ≥3-of-4) AND WHEN (MT1–MT3, ≥2-of-3). Those gaps are
documented in §5 as additional degrees of freedom.

**Why Option C (separate doc, not amendment):**
- Option A (amend §1) would rewrite a lock-before-look spec post-data — forbidden.
- Option B (wire MT1–MT3 then gate) would launder already-seen 2020–2024 data into a
  fresh-looking gate run — also forbidden.
- Option C creates a new, self-contained locked spec for the built code. The §9
  verdict-reading rule (A1_SMC_MOMENTUM_DECISION.md) applies unchanged.

**Verdict-reading rule:** §9 of A1_SMC_MOMENTUM_DECISION.md — per-instrument, no pooling,
all instruments reported together in A1_WHERE_ONLY_GATE_RESULT.md.

---

## §1 — ALPHA DESIGN (exact implementation; do not modify after data exposure)

Entry fires on an H1 bar when **all five** filters are simultaneously satisfied:

### Filter 1 — Liquidity Sweep
`LiquidityDetector(swing_lookback=5, cluster_atr_mult=0.3, atr_window=14)`

A swing high/low cluster (equal highs/lows within `0.3 × ATR(14)` of each other, using
past-only lookback of 5 bars) has been swept: price closes beyond the cluster level.

### Filter 2 — Structure Break (ChoCH preferred; BOS accepted)
`BosChochDetector(swing_lookback=5, atr_window=14)`

A Change of Character (ChoCH) or Break of Structure (BOS) is present on the window.
Trade direction = direction of the most recent ChoCH/BOS event.

### Filter 3 — Order Block at Current Price
`OrderBlockDetector(displacement_atr_mult=1.5, atr_window=14, lookback=5)`

An **unmitigated** OB exists whose range contains the current close. An OB is identified
as the last opposing candle before a displacement candle whose body ≥ `1.5 × ATR(14)` that
also breaks the prior swing high/low within 5 bars.

**Mitigation rule (close-through):** bullish OB consumed when close < OB.low;
bearish OB consumed when close > OB.high.

### Filter 4 — Fair Value Gap
`FairValueGapDetector(min_size_atr=0.5, atr_window=14)`

An **unmitigated** FVG is present. Definition (3-candle pattern):
- Bullish FVG: `candle[i].low > candle[i-2].high`, gap ≥ `0.5 × ATR(14)`
- Bearish FVG: `candle[i].high < candle[i-2].low`, gap ≥ `0.5 × ATR(14)`

Mitigation: FVG consumed when price closes inside or through the gap.

### Filter 5 — Displacement Candle
`DisplacementDetector(atr_mult=1.8, atr_window=20)`

A displacement candle is present in the window: `body ≥ 1.8 × ATR(20)`.
Note: this detector uses `atr_window=20`, independent of the `atr_window=14` used by
Filters 1–4.

### Entry parameters (backtest harness)
- Stop distance: 0.5% (fixed placeholder — real SL from OB range in production)
- Target distance: 1.0% (fixed placeholder — real TP in production)
- Position size: 0.5% account risk (RiskEngine default)

### What is NOT implemented in this alpha

| Full-A1 spec element | Status here |
|---|---|
| Regime gate (ADX(14)>25 + EMA200 slope) | OMITTED |
| ATR floor (ATR% ≥ 0.3%) | OMITTED |
| Z4: Fib 61.8–78.6% retracement | OMITTED; FVG used instead |
| Z2: Volume spike at OB candle | NOT-TESTED (no CME volume data) |
| WHERE confluence ≥3-of-4 of Z1–Z4 | OMITTED; all-required AND logic used |
| MT1: engulfing/pin bar | OMITTED |
| MT2: RSI(14) divergence | OMITTED |
| MT3: EMA(8) slope | OMITTED |
| WHEN threshold ≥2-of-3 of MT1–MT3 | OMITTED |

---

## §2 — INSTRUMENT AND DATA

**Primary:** GC continuous (GC.c.0, GLBX.MDP3), 1m resampled to 1h.
  Cached: `/home/aungp/data/cache/GC_1h.parquet` — 10,451 bars, 2020-01-02→2024-12-30

**Secondary:** 6E continuous (6E.c.0, GLBX.MDP3), 1m resampled to 1h.
  Cached: `/home/aungp/data/cache/6E_1h.parquet` — 24,441 bars, 2020-01-02→2024-12-30

Per-instrument models only. GC and 6E are never pooled.

---

## §3 — IS/OOS SPLIT (locked before gate run; do not adjust post-data)

Chronological 60/40 split, identical for both instruments:

```
IS period:  2020-01-02 → 2022-12-30  (3 years, ~60% of window)
OOS period: 2023-01-02 → 2024-12-30  (2 years, ~40% of window)

IS_CUTOFF_DATE = 2022-12-30
```

CPCV, purged walk-forward, and Monte Carlo are computed on **OOS only**.
IS bars may not be examined for verdict purposes after this line.

---

## §4 — NET-OF-COST MODEL

| Instrument | Preset | spread_r | commission_r | slippage_r | total_r |
|---|---|---|---|---|---|
| GC | `CostModel.for_gc()` | 0.07 | 0.05 | 0.06 | **0.18R** |
| 6E | `CostModel.for_6e()` | 0.04 | 0.04 | 0.04 | **0.12R** |

Net-of-cost PF is the only PF that counts. Gross PF > 1.25 alone is NOT sufficient for ROBUST.

---

## §5 — TRIAL COUNT (n_trials floor; computed before gate run)

### Inherited DoF from parent A1 spec (A1_SMC_MOMENTUM_DECISION.md §5)

All 14 pre-registered parent DoF carry forward. They represent parameters and thresholds
considered during the development of this alpha — including those ultimately omitted.
Considering-and-rejecting a parameter is not free; it still inflates the search space.

| Parameter / threshold | Count |
|---|---|
| Regime ADX threshold (25) | 1 |
| EMA200 slope window (5-bar) | 1 |
| ATR% floor (0.3%) | 1 |
| ATR-slope window (10-bar) | 1 |
| Session filter (off) | 1 |
| WHERE threshold ≥3-of-4 zone signals (primary) | 1 |
| WHERE threshold ≥2-of-4 zone signals (secondary trial) | 1 |
| OB stale rule (close-through) | 1 |
| Fib levels 0.618–0.786 (considered; FVG substituted) | 1 |
| RSI divergence lookback 20-bar (considered; WHEN omitted) | 1 |
| IS/OOS cutoff | 1 |
| WHEN threshold ≥2-of-3 momentum signals (considered; WHEN omitted) | 1 |
| EMA momentum span (8) (considered; MT3 omitted) | 1 |
| EMA slope lookback (3-bar) (considered; MT3 omitted) | 1 |

Subtotal: **14**

### Additional DoF specific to A1_WHERE_ONLY (unlogged in parent; registered here)

These were present in the code but not pre-committed anywhere before this document.
Each is a real design choice or numeric parameter that was not searched away — but
"not searched" must be verified by the builder, not assumed.

| Decision / parameter | Value | Rationale for +1 |
|---|---|---|
| FVG substituted for Fib Z4 | FVG(min=0.5 ATR) | Filter composition choice; alternative (Fib) was in parent spec |
| WHEN trigger omitted | (entire MT1-3 block) | Design choice deviating from parent spec |
| Regime gate omitted | (ADX+EMA200 block) | Parent spec assumed regime ON; this omits it |
| ATR floor omitted | (ATR%≥0.3% block) | Parent spec assumed ATR floor ON; this omits it |
| OB `displacement_atr_mult` | 1.5 | Numeric param; not in any prior locked doc |
| Displacement `atr_mult` | 1.8 | Numeric param; not in any prior locked doc |
| Displacement `atr_window` | 20 | Separate window from main atr_window=14; not in prior doc |
| FVG `min_size_atr` | 0.5 | Numeric param; not in any prior locked doc |
| Liquidity `cluster_atr_mult` | 0.3 | Numeric param; not in any prior locked doc |

Subtotal: **9**

### Floor

```
n_trials = max(configs_actually_evaluated, 23)
```

**Floor: 23.** DSR z-score must be computed at `n_trials = 23` minimum.
If any additional configs were evaluated before the gate run, increment accordingly
and log in A1_WHERE_ONLY_GATE_RESULT.md.

---

## §6 — GATE CRITERIA (identical to GATE_DECISION.md — no special treatment)

| Dimension | READ floor | ROBUST (required for capital allocation) |
|---|---|---|
| OOS trades (n) | ≥ 50 | ≥ 200 |
| Profit factor | > 1.0 gross | > 1.25 net-of-cost |
| Win rate | — | > 45% |
| Sharpe | — | > 1.2 |
| Max drawdown | — | < 15% |
| CPCV median PF | — | > 1.0 |
| Purged WF folds | — | ≥ 60% with PF > 1 |
| MC 5th-pct PF | — | > 0.9 |
| Deflated Sharpe z | — | > 0 (n_trials ≥ 23) |

**FRAGILE** if OOS n < 50 or any READ-floor check fails.
Gate (`run_gate.py`) cannot run if OOS n < 50 — record as FRAGILE directly.

---

## §7 — FRAGILE HANDLING

| Outcome | Action |
|---|---|
| FRAGILE (n<50 or floor fails) | Archive `research_archive/a1_where_only/` with FRAGILE header. Record finding. |
| READ | A1_WHERE_ONLY contributes context to A3 (0.4 weight). Not standalone-deployable. |
| ROBUST | Advance per §9 of A1_SMC_MOMENTUM_DECISION.md. |

FRAGILE is **never re-promoted**. A1_WHERE_ONLY FRAGILE confirms that WHERE-only SMC
signals have no standalone edge on CME H1 futures — consistent with
`research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md` and A0_MVP.

If FRAGILE on all gated instruments: **A2 carries the gate race** (ROADMAP Rule 2).
The full-A1 spec (A1_SMC_MOMENTUM_DECISION.md §1, WHERE+WHEN) remains as an
unbuilt hypothesis requiring a fresh, held-out data window to be valid.

---

## §8 — AMENDMENT LOG (append only)

- 2026-06-14: Initial lock. Created because A1SmcMomentum code does NOT implement the
  full A1 spec (A1_SMC_MOMENTUM_DECISION.md §1). The built code is WHERE-only.
  Five numeric params pre-registered retrospectively (+5 DoF). Four design-omission choices
  registered (+4 DoF). n_trials floor = 23 (14 inherited + 9 additional).
  IS_CUTOFF_DATE = 2022-12-30 locked before gate run.
  Data: GC+6E 1h 2020-2024 cached (Databento GLBX.MDP3). Gate run authorized.
