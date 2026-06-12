# FILTERED-SMC GATE DECISION — G0 SPEC LOCK
# Dispatch 2 | Committed BEFORE any alpha sees G1 data.
# Date locked: 2026-06-12
# DO NOT MODIFY thresholds or signal definitions after any alpha has seen the validation dataset.
# Changing any definition below = NEW TRIAL (increment n_trials in §2).

---

## §0 — INSTRUMENT PIN (from Dispatch 1 BLOCKED verdict)

**G1 instrument: BLOCKED**

Dispatch 1 found: no real-volume GC/MGC or 6E history, no delta series, old engine
lacks trial-count-aware DSR. G1 cannot run until Dispatch 3a completes.

When Dispatch 3a resolves:
- READY → instrument = GC/MGC + 6E (Databento, real CME volume)
- CAVEATED → available instrument, with delta-trigger + volume-filter marked NOT-TESTED
  (they cannot silently count as "passed" on proxy/absent data)
- BLOCKED remains until a real-volume source is wired

**This file is locked with instrument = BLOCKED. Dispatch 3a will add an amendment
entry at the bottom when resolved — not modify existing sections.**

---

## §1 — FIVE-FILTER SPEC (frozen)

FILTERED-SMC = all 5 filters applied before any entry is considered.

### Filter 1: Regime gate
- Condition: ADX(14) > 25 (trending) AND EMA200 slope positive (long bias) OR negative (short bias)
- ADX period: 14 (fixed)
- ADX threshold: 25 (fixed — below this = ranging/chop, SMC unreliable)
- EMA200 slope window: 5-bar look-back on daily closes (fixed)
- Pass = BOTH sub-conditions met for the intended direction

### Filter 2: Volatility floor (ATR%)
- ATR period: 14 (fixed)
- ATR% = ATR(14) / close × 100
- Floor threshold: ATR% ≥ 0.3% (fixed — below this, bid-ask cost eats the grid)
- Optional ceiling: ATR% ≤ 5.0% (fixed — above this, SL sizing breaks down; default OFF,
  can be enabled as a separate trial — enabling = +1 to n_trials)
- Pass = ATR% ≥ 0.3% (and ≤ 5.0% if ceiling enabled)

### Filter 3: ATR-slope (momentum confirmation)
- Window: 10-bar look-back on ATR(14) values (fixed)
- Threshold: ATR slope must be positive (ATR expanding, not contracting)
- Computed as: linear regression slope of last 10 ATR(14) values > 0
- Pass = slope > 0

### Filter 4: Session filter
- Default: OFF (session filter disabled — all hours eligible)
- Enabling session filter = separate trial (+1 to n_trials per session window tested)
- If OFF, pass = always

### Filter 5: Selection gate (signal-set)
- Two thresholds tested (both registered here; choosing one post-data = +1 trial already counted):
  - Strict: ≥ 3-of-4 zone + trigger signals required
  - Relaxed: ≥ 2-of-4 zone + trigger signals required
- The gate evaluation uses BOTH thresholds; only the pre-registered one counts for the verdict
- Pre-registered primary threshold: **≥ 3-of-4** (strict)
- Relaxed (≥ 2-of-4) is a secondary trial; both count toward n_trials

### Risk parameters (frozen)
- Risk per trade: 0.5% of equity (fixed)
- Max single-trade loss: 2.0% (fixed hard stop beyond SL)
- Drawdown halt: 5.0% cumulative loss → halt session (fixed)
- Max concurrent positions: 2 (fixed)
- Consecutive-loss halt: 6 losses in sequence → pause 24h (fixed)

---

## §2 — SIGNAL DEFINITIONS (frozen — changing any = new trial)

Four zone signals + four trigger signals = 8 binary inputs to Filter 5.

### Zone signals (WHERE — structural context)

**Z1: Order Block**
- Definition: A candle (or 2-candle cluster) where price consolidated BEFORE a
  Break-of-Structure move. Specifically: the last up-candle (for bearish OB) or
  last down-candle (for bullish OB) before the BOS candle, on the working timeframe.
- Working timeframe: H1 (fixed for this trial)
- Valid OB zone: the HIGH-LOW range of the qualifying OB candle(s)
- Stale rule: OB is invalidated if price closes THROUGH the zone (not just wicked)
- Z1 = 1 if price is currently retesting a valid OB zone (price within HIGH-LOW of OB candle)

**Z2: Volume Spike at zone**
- Definition: The OB candle's volume ≥ 1.5× the 20-bar rolling average volume at that candle
- Volume type: the available instrument's volume column (see §0 — if CAVEATED, this is proxy/absent)
- Threshold: 1.5× (fixed)
- If no real volume available: Z2 = NOT-TESTED (cannot be evaluated; see §0 instrument pin)
- Z2 = 1 if the OB candle that defines Z1 had volume ≥ 1.5× 20-bar avg

**Z3: Break of Structure (BOS)**
- Definition: A candle close ABOVE (bullish BOS) or BELOW (bearish BOS) the most recent
  swing high or swing low on the working timeframe (H1)
- Swing detection: swing_length = 5 bars (fixed — 5 bars left, 5 bars right)
- BOS must be the candle that preceded the retracement now retesting the OB zone (Z1)
- BOS must be within the last 20 bars from the retest point (recency rule, fixed)
- Z3 = 1 if a qualifying BOS exists within 20 bars before the Z1 retest

**Z4: Premium / Discount zone**
- Definition: Fibonacci retracement of the BOS impulse move
  - Discount zone (long): retest in the 0.618–0.786 Fibonacci level of the impulse leg up
  - Premium zone (short): retest in the 0.618–0.786 Fibonacci level of the impulse leg down
- Fib levels: 61.8% and 78.6% (fixed)
- Z4 = 1 if the current retest is between the 61.8% and 78.6% retracement of the BOS impulse

### Trigger signals (WHEN — entry timing)

**T1: Engulfing / Rejection candle**
- Definition: At the retest of the OB zone (Z1), the entry candle must be either:
  - A bullish engulfing (close > open of prior candle, body ≥ 60% of range) for longs
  - A bearish engulfing (close < open of prior candle, body ≥ 60% of range) for shorts
  - OR a pin bar (wick ≥ 2× body, close on opposite side of wick from zone)
- Measured on the working timeframe (H1)
- T1 = 1 if entry candle meets engulfing or pin-bar definition

**T2: RSI divergence**
- Definition: RSI(14) shows bullish divergence (lower price low, higher RSI low) for longs,
  or bearish divergence (higher price high, lower RSI high) for shorts
- RSI period: 14 (fixed)
- Lookback for divergence: 20 bars (fixed)
- T2 = 1 if divergence is present within 20 bars of entry

**T3: Volume confirmation at trigger**
- Definition: The trigger candle (T1 candle) volume ≥ 1.0× the 20-bar rolling average
- Threshold: 1.0× (fixed — at or above average)
- If no real volume available: T3 = NOT-TESTED (same caveat as Z2)
- T3 = 1 if trigger candle volume ≥ 20-bar avg

**T4: Delta imbalance**
- Definition: Net delta (buy volume − sell volume) for the trigger candle confirms direction:
  positive net delta for longs, negative for shorts
- Requires bid-ask / tape data to compute delta — NOT available on current data (see §0)
- If delta series absent: T4 = NOT-TESTED
- T4 = 1 if delta sign matches intended direction

### Signal-set membership
- Zone set: {Z1, Z2, Z3, Z4} — 4 binary signals
- Trigger set: {T1, T2, T3, T4} — 4 binary signals
- Required for entry per Filter 5: ≥3-of-4 from EACH set (primary) or ≥2-of-4 (secondary trial)
- NOT-TESTED signals count as 0 (absent, not as a pass)

---

## §3 — TRIAL COUNT (frozen)

Trial count (n_trials) for Deflated Sharpe calculation.

### Base degrees of freedom

| Parameter / threshold tested | Count |
|---|---|
| Regime threshold (ADX 25) | 1 |
| EMA slope window (5-bar) | 1 |
| ATR% floor (0.3%) | 1 |
| ATR% ceiling (optional, default off) | 1 |
| ATR-slope window (10-bar) | 1 |
| Session filter (off vs on) | 1 |
| Selection threshold ≥3-of-4 (primary) | 1 |
| Selection threshold ≥2-of-4 (secondary) | 1 |
| OB stale rule (close-through vs wick-through) | 1 |
| Fib levels 0.618–0.786 (one threshold band) | 1 |
| RSI divergence lookback (20-bar) | 1 |

**Minimum floor (summed DoF): 11**

### Rule
n_trials = max(configs_actually_evaluated, 11)

Any grid search or sweep MULTIPLIES the count:
- Each distinct parameter combination evaluated = +1 trial
- Example: if ATR% floor tested at {0.2%, 0.3%, 0.5%} = +2 additional trials (3 total for that param)
- The realized n_trials from the actual G1 run must be logged in the G1 result file

**Deflated Sharpe fails to deflate if n_trials is under-counted. Do not under-count.**

---

## §4 — GATE CRITERIA (frozen)

### LEVEL test (must pass for any ROBUST verdict)
Source: `ag/validation/lock_before_look/GATE_DECISION.md` (v4 gate — authoritative)

| Dimension | Floor (READ) | ROBUST |
|---|---|---|
| Trades (n) | ≥ 50 | ≥ 200 |
| Profit factor (net of fees) | > 1.0 gross | > 1.25 NET |
| Win rate | — | > 45% |
| Sharpe ratio | — | > 1.2 |
| Max drawdown | — | < 15% |
| CPCV median PF | — | > 1.0 |
| Purged WF folds PF > 1 | — | ≥ 60% |
| MC 5th-pct PF | — | > 0.9 |
| Deflated Sharpe z (trial-count-aware) | — | > 0 |

Cost model: per `ag/validation/lock_before_look/GATE_DECISION.md` — CME commission + spread +
slippage for GC/MGC or 6E. Net-of-cost PF is the only PF that counts.

### MARGINAL test
FILTERED-SMC net-of-fee PnL (OOS) > unfiltered-SMC-baseline net-of-fee PnL (OOS)
on the SAME OOS window. Both must be evaluated.

### Binding rule
**No future revision may drop the LEVEL conditions and keep only the beat-baseline test.**
Both LEVEL and MARGINAL must pass for a ROBUST verdict.

### Missing DSR in old engine
Dispatch 1 confirmed innovative_backtest_engine.py lacks trial-count-aware DSR.
**G1 prerequisite: use `ag/validation/deflated_sharpe.py` (v4 engine) for DSR calculation.**
If G1 is run before this is wired, the DSR check must be computed separately and appended
to the G1 result. Running the old engine alone and claiming a G1 pass is NOT sufficient.

---

## §5 — VERDICTS AND HANDLING

| Outcome | Action |
|---|---|
| ROBUST (all LEVEL + MARGINAL pass) | May proceed to paper trading (30-day dry-run first) |
| FRAGILE (any LEVEL fails) | Move to `research_archive/` with FRAGILE header. NOT discarded, never re-promoted. Draft note folding filtered-SMC to a CONTEXT INPUT for a future ensemble — not a standalone entry |
| BLOCKED (data not available) | Wait for Dispatch 3a. No verdict possible. |

**A FRAGILE verdict is FINAL for SMC-as-standalone-edge.**
Do NOT tune-and-retry into a v7. If FRAGILE, document as CONTEXT INPUT only.

---

## §6 — AMENDMENT LOG (append only — do not modify above sections)

- 2026-06-12: Initial lock. Instrument = BLOCKED pending Dispatch 3a (Databento/CME wiring).
  Dispatch 1 found: 65-day Bybit perp data only; no real CME volume; no delta series; old engine
  lacks trial-count-aware DSR. G1 prerequisite list in G1_DATA_READINESS.md.
