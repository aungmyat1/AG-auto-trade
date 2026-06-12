# RESEARCH ARCHIVE — ALiVMassit
# Verdict: FRAGILE (82.7% WR / PF 0.14 — high win rate ≠ edge)
# Date archived: 2026-06-12
# DO NOT RE-TEST. Validated negative result.

---

## Strategy Description

ALiVMassit: a high-frequency reversal strategy targeting XAUUSD with a high win rate achieved
by taking very small winners and letting losers run (or cutting large). The name is derived
from the indicator combination used (ALMA + Voss filter + MA crossover).

## Why It Failed

**Win rate ≠ edge.** The strategy achieved 82.7% win rate — which appears impressive — but
the profit factor was 0.14, indicating the average loss was ~5.5× the average win. The
few large losses completely overwhelmed the stream of small wins.

This is the canonical "picking up pennies in front of a steamroller" failure mode:
- 82.7% of trades: small +R
- 17.3% of trades: large −R (approx 5.5× average winner)
- Net PF = 0.14 (catastrophically below 1.0)

## Gate Scorecard

| Check | Result |
|---|---|
| n ≥ 50 | PASS |
| gross PF > 1.0 | **FAIL (PF = 0.14)** |
| All ROBUST checks | Not evaluated (floor failed) |

**Verdict: FRAGILE** (gross-negative at the floor level)

## Lesson

Win rate is not a proxy for edge. A strategy with 99% win rate and PF = 0.01 loses money.
The validation gate correctly filters this: PF must exceed 1.0 GROSS before any ROBUST check
is even evaluated.

**Never optimize for win rate directly.** The gate targets net PF > 1.25, Sharpe > 1.2,
and DSR > 0 — metrics that cannot be gamed by asymmetric sizing the way win rate can.

## Prohibition

Archived per GROUND_TRUTH.md rule 2. Any "ALiVMassit v2 with adjusted R:R" is a new trial.
