# A1 SMC-FILTER + MOMENTUM GATE DECISION — G0 SPEC LOCK
# Committed BEFORE any gate run or alpha code. Do NOT modify thresholds after any alpha has seen data.
# Changing any definition below = NEW TRIAL (increment n_trials in §4).
# Date locked: 2026-06-12

---

## §0 — DATA STATUS: BLOCKED

**A1 gate run is BLOCKED pending Databento/CME data wiring.**

Per `docs/validation/G1_DATA_READINESS.md`:
- Real-volume GC/MGC or 6E history not present (stub only: `ag/data/databento/__init__.py`)
- Delta / order-flow series absent
- Only 65-day Bybit perp data available — insufficient

**A1 code may be built against this spec, but no gate run may be claimed until:**
1. Real-volume GC/MGC or 6E data (≥2y, CME-sourced) wired into `ag/data/databento/`
2. Owner approves Databento subscription (see G1_DATA_READINESS.md §5 HOLD note)
3. `ag/validation/` stack confirmed as the engine (not legacy `innovative_backtest_engine.py`)

**Amendment entry (§7) must be added when data becomes available — not modification of §0.**

---

## §1 — ALPHA DESIGN (non-negotiable structure)

A1 = **SMC context filter (WHERE) + momentum trigger (WHEN)**.

- WHERE: smart money context indicators tell where price is likely to react (OB, BOS, FVG, Fib).
  These are passive — they NEVER generate entries on their own.
- WHEN: momentum/delta indicators confirm that the WHERE zone is active NOW.
  These are the entry triggers.

### SMC WHERE filter (signal spec)

Full spec locked in `docs/validation/FILTERED_SMC_DECISION.md` (referenced, not duplicated).

WHERE requires ≥3-of-4 zone signals (Z1–Z4) to be active (primary threshold, §3 locked):
- Z1: Order Block (OB) retest
- Z2: Volume spike at OB candle (NOT-TESTED if no real volume — see §0)
- Z3: Break of Structure (BOS) within 20 bars
- Z4: Fibonacci discount/premium zone (61.8%–78.6% retracement)

NOT-TESTED signals count as 0 (absent), not as a pass.

### Momentum WHEN trigger

The WHEN trigger is the A1-specific addition on top of the WHERE filter.
Entry fires ONLY when both WHERE (≥3-of-4 zone) AND WHEN are satisfied.

**WHEN = ≥2-of-3 momentum confirmation signals (any two of MT1, MT2, MT3):**

**MT1: Trigger candle quality (from FILTERED_SMC_DECISION T1)**
- Bullish engulfing (close > prior open, body ≥ 60% range) for longs
- Bearish engulfing (close < prior open, body ≥ 60% range) for shorts
- OR pin bar (wick ≥ 2× body, close opposite the zone)
- Measured on H1. MT1 = 1 if entry candle meets criteria.

**MT2: RSI divergence (from FILTERED_SMC_DECISION T2)**
- RSI(14) bullish divergence (lower price low, higher RSI low) for longs
- RSI(14) bearish divergence (higher price high, lower RSI high) for shorts
- Lookback: 20 bars. MT2 = 1 if divergence present within 20 bars.

**MT3: Momentum slope**
- Definition: EMA(8) of close is rising (long) or falling (short) on the entry bar
- EMA span: 8 (fixed)
- Slope: EMA(8) current bar > EMA(8) 3 bars ago (for long), < for short
- MT3 = 1 if slope confirms direction of intended trade

Note: T3 (volume at trigger) and T4 (delta imbalance) from FILTERED_SMC_DECISION are
NOT-TESTED until CME volume + delta data is available. They are excluded from A1's WHEN
trigger for now. Including them later = +1 trial per included signal.

### Regime gate (pre-filter)

ADX(14) > 25 AND EMA200 slope positive (longs) or negative (shorts).
This runs BEFORE any Z/T/MT evaluation — if regime fails, no signal.
Parameters identical to FILTERED_SMC_DECISION §1 Filter 1 (already counted in trial floor).

### ATR floor

ATR% ≥ 0.3% (fixed). Same as FILTERED_SMC_DECISION §1 Filter 2.

---

## §2 — AlphaModule INTERFACE

A1 exposes: `propose(market_data: dict) -> Optional[SignalProposal]`

Signal generation rule (replay mode for gate; live mode for paper trading):
- At bar close, evaluate all WHERE and WHEN signals
- If ≥3-of-4 WHERE signals AND ≥2-of-3 WHEN signals AND regime passes AND ATR floor passes:
  - Propose a BUY or SELL SignalProposal
- Otherwise: return None

```python
class A1SmcMomentum(AlphaModule):
    alpha_id = "A1"
    is_ready() → False until ROBUST verdict

    def propose(self, market_data: dict) -> Optional[SignalProposal]:
        # 1. Regime check (ADX + EMA200 slope)
        # 2. ATR floor check
        # 3. Evaluate Z1–Z4 (count where signals)
        # 4. Evaluate MT1–MT3 (count momentum signals)
        # 5. If both thresholds met → propose entry
```

---

## §3 — IS/OOS SPLIT (to be resolved when data is available)

**IS/OOS split type:** chronological, by date.

**IS period target:**
- Start: first available GC or MGC bar in Databento data
- End: IS_CUTOFF_DATE (to be set as the date at which the cumulative signal count first reaches 200)
- Minimum IS signals required: 200 (per GATE_DECISION.md ROBUST floor)

**OOS period target:**
- Start: IS_CUTOFF_DATE
- End: last available bar
- Minimum OOS signals required: 200 (ROBUST floor)

**IS_CUTOFF_DATE is NOT set until data is loaded.** It must be set to guarantee ≥200 IS AND
≥200 OOS signals BEFORE the OOS window is looked at. This is the critical lock-before-look step.

The IS_CUTOFF_DATE, once set, becomes a +1 DoF (counted in §4 trial floor already).

**Symbol preference:** GC (front-month continuous, back-adjusted). MGC acceptable but must be
documented. Per-instrument models only — never combine GC and MGC signals into one curve.

---

## §4 — EXECUTION-HONESTY MODEL

**Instrument:** GC (CME Gold futures, 100 oz/contract)
**Commission:** $2.50 per side ($5 round-trip) per contract — standardized CME rate
**Spread:** typically 0.1–0.2 ticks at liquid hours; use 0.2 ticks ($0.20) per side
**Slippage:** 0.5 ticks ($0.50) per side — conservative for H1 signals
**Total round-trip cost:** ($5 + $0.40 + $1.00) = $6.40/contract = ~0.064%/contract at $10,000/oz

**In R-multiples (reference = SL distance):**
```
total_cost_r = total_cost_$ / (sl_pips × pip_value)
```
For typical GC H1 SL of 10 ticks: `cost_r = $6.40 / (10 × $10) = 0.064R/trade`

Use `CostModel.for_gc()` from `ag/validation/cost_model.py` — the preset encodes these values.

**Net-of-cost PF is the ONLY PF that counts.** Gross PF > 1.25 is NOT sufficient for ROBUST.

---

## §5 — TRIAL COUNT (frozen floor)

### Base degrees of freedom

| Parameter / threshold tested | Count |
|---|---|
| Regime ADX threshold (25) | 1 |
| EMA200 slope window (5-bar, from FILTERED_SMC spec) | 1 |
| ATR% floor (0.3%) | 1 |
| ATR-slope window (10-bar) | 1 |
| Session filter (off) | 1 |
| WHERE threshold ≥3-of-4 zone signals (primary) | 1 |
| WHERE threshold ≥2-of-4 zone signals (secondary trial) | 1 |
| OB stale rule (close-through) | 1 |
| Fib levels 0.618–0.786 | 1 |
| RSI divergence lookback (20-bar) | 1 |
| IS/OOS cutoff (to be set — pre-counted) | 1 |
| WHEN threshold ≥2-of-3 momentum signals | 1 |
| EMA momentum span (8) | 1 |
| EMA slope lookback (3-bar) | 1 |

**Floor: 14**

### Rule
```
n_trials = max(configs_actually_evaluated, 14)
```

Any grid/sweep MULTIPLIES the count:
- Testing 3 EMA spans for MT3 = +2 trials
- Including T3/T4 once available = +1 per signal included
- Testing ≥2-of-3 vs ≥1-of-3 WHEN threshold = +1 trial

**The realized n_trials from the actual A1 gate run must be logged in A1_GATE_RESULT.md.**

---

## §6 — GATE CRITERIA (identical to A2/A3 — no special treatment for A1)

Same v4 gate thresholds as `GATE_DECISION.md`:

| Dimension | Floor (READ) | ROBUST |
|---|---|---|
| Trades (n OOS) | ≥ 50 | ≥ 200 |
| Profit factor (net of execution-honesty model) | > 1.0 gross | > 1.25 NET |
| Win rate | — | > 45% |
| Sharpe ratio | — | > 1.2 |
| Max drawdown | — | < 15% |
| CPCV median PF | — | > 1.0 |
| Purged WF folds PF > 1 | — | ≥ 60% |
| MC 5th-pct PF | — | > 0.9 |
| Deflated Sharpe z (trial-count-aware, n_trials=14) | — | > 0 |

### MARGINAL test (from FILTERED_SMC_DECISION §4)
A1 net-of-cost OOS PF > unfiltered baseline OOS PF on the same OOS window.
Both evaluated. Failing only the MARGINAL while passing LEVEL = READ (not ROBUST).

---

## §7 — FRAGILE / BLOCKED HANDLING

| Outcome | Action |
|---|---|
| BLOCKED (no data) | Gate run deferred. A1 code may be built, `is_ready()→False`. |
| FRAGILE (floor fails) | Archive in `research_archive/` with FRAGILE header. A1 feeds A3 as 0.4 weight context input, not a standalone entry. |
| READ | A1 contributes to A3 ensemble. `is_ready()→False` standalone. |
| ROBUST | A1 cleared for paper trading. Owner reviews before live. |

Per GROUND_TRUTH.md: FRAGILE is never re-promoted. Tightening or relaxing thresholds to
rescue a FRAGILE verdict is BANNED.

---

## §8 — AMENDMENT LOG (append only)

- 2026-06-12: Initial lock. Status BLOCKED — no Databento/CME data. A1 code build authorized
  against this spec; gate run deferred until real-volume GC data is wired and owner approves
  Databento subscription. Trial floor = 14.
  WHERE spec references docs/validation/FILTERED_SMC_DECISION.md (unchanged).
  WHEN = ≥2-of-3 of {MT1: engulfing/pin, MT2: RSI divergence, MT3: EMA8 slope}.
  T3/T4 (volume + delta) excluded until CME data available.
