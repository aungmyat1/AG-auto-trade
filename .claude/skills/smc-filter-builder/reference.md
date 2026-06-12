# SMC Detection Reference (filter-only)

Definitions for the A1 context filter. One definition per concept; alternatives are new
counted trials. All detection runs on **closed bars only**. Defaults below are the
pre-registered starting points — identical across GC/MGC/6E.

## Timeframe flow (v4 plan)

```
Daily bias  →  H1 trend filter  →  M15 zones (this filter)  →  M5 trigger (momentum side)
```

- **Daily bias:** up if daily close > daily 50EMA, down if below — else NO_TRADE.
- **H1 trend:** long context requires H1 close > session VWAP AND > H1 50EMA (short = mirror).
  Disagreement with daily bias = NO_TRADE.
- **Regime pre-gate (owned by ag/regime/, not SMC):** ADX>25 AND ATR expanding AND
  volume > 20-bar avg, else the whole stack stands down.

## Zone vote — context requires ≥ 2 of 4 agreeing with bias direction

| # | Condition | Definition |
|---|---|---|
| 1 | Order block | see OB below, ACTIVE state, price inside or first touch |
| 2 | FVG | see FVG below, < 50% filled, price inside |
| 3 | Prior-session H/L | price within `prox_ticks` of previous session's high (short ctx) / low (long ctx) |
| 4 | Session-open sweep | sweep (below) of the session-open level or session extreme |

(The trigger vote — BOS · volume spike · VWAP reclaim · delta imbalance, ≥3 of 4 — belongs
to the momentum module, NOT here. BOS is one trigger vote, never a standalone entry.)

## Detectors

### Swing points
N-bar fractal: bar `i` is a swing high if `high[i]` > highs of N bars on each side
(default **N=3**). Confirmed only at bar `i+N` — that lag is real and must not be backfilled.

### Order block (OB)
Last opposite-direction candle immediately before a **displacement**: a move whose range ≥
`disp_atr_mult` × ATR(14) (default **1.5**) AND that closes beyond the nearest confirmed
swing. Bullish OB = last down candle before an up displacement; bearish = mirror.

- Zone bounds: the candle **body** (open↔close), not the full wick range.
- States (one-way): `ACTIVE` → `MITIGATED` (any later bar trades into the zone) →
  `INVALIDATED` (a bar **closes** through the far side). Expiry: **96** M15 bars.
- **Multi-OB tracker:** keep top-10 ACTIVE OBs per instrument, ranked by displacement
  strength, freshness, and confluence with other zone conditions. Drop the weakest on
  overflow — never track unbounded lists.

### Fair value gap (FVG)
Three consecutive closed bars; bullish FVG when `low[i] > high[i-2]` — zone =
`(high[i-2], low[i])`, minimum size `fvg_min_ticks` (default **4** GC ticks / **2** 6E ticks
— tick-size scaled, not hand-tuned). Track filled fraction; ≥50% filled = consumed.
Bearish = mirror.

### Liquidity sweep
A bar whose extreme pierces a reference level (confirmed swing H/L, prior-session H/L,
session open) by ≥ `sweep_ticks` (default **2**) and then **closes back inside** the level.
Confirmed only on that close — an open excursion is not a sweep. A sweep flips the zone
vote in the *reversal* direction (sweep of lows supports LONG context).

### BOS / ChoCH (context labels only)
Close beyond a confirmed swing: with-trend = BOS (continuation label), against-trend =
ChoCH (possible reversal label). In this repo these are **state labels and one trigger
vote** — `ChoCH → entry` is the archived FRAGILE pattern and must never be implemented.

### Premium / discount
Over the last `range_bars` (default **96** M15 bars): equilibrium = (range high+low)/2.
LONG_ALLOWED preferred only in discount (below eq), SHORT_ALLOWED in premium. Acts as a
veto: bias+zones in premium for a long = NO_TRADE.

## Sessions (UTC — must match `ag/config.py`)

- GC/MGC: London 07:00–09:30, NY 13:30–16:00
- 6E: London 07:00–12:00, overlap 12:00–16:00
- Outside windows, and ±30 min around HIGH_IMPACT_EVENTS (NFP, CPI, FOMC, ECB, BOE, GDP):
  filter returns NO_TRADE regardless of zones.

## Anti-look-ahead checklist (every detector, every PR)

1. Inputs end at the last **closed** bar; the forming bar is never visible.
2. Swing/zone confirmation lag respected — nothing is known before its confirm bar.
3. No repainting: once emitted, a zone's bounds never change; states move one-way.
4. Appending future bars must not alter any past output (regression test required).
5. Session/prior-day levels computed from completed sessions only.

## Parameter ledger

Every default above, and every variant ever tried, is a row in
`ag/alpha/a1_smc_momentum/TRIALS.md` (param, value, date, reason, outcome). That row count
is the floor for `--n-trials` in the gate. An unlogged experiment is self-deception.
