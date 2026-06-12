# RESEARCH ARCHIVE — Dual-Mode Scalper
# Verdict: REVERTED (scalpers never fired — 0/100 trades in demo)
# Date archived: 2026-06-12
# DO NOT RE-TEST. Validated negative result.

---

## Strategy Description

Dual-mode scalper: a strategy designed to operate in two modes — a "scalp" mode for ranging
markets and a "trend follow" mode for breakouts. XAUUSD on sub-hourly timeframes.

The concept: regime detection triggers mode switching, allowing one strategy to adapt to
both trending and ranging conditions.

## Why It Failed

**Scalpers never fired.** In 100 demo trades:
- 0 scalp-mode entries executed
- Trend-mode entries executed but were reverted (regime filter repeatedly blocked)

Root cause: the regime filter and scalp entry conditions were mutually exclusive in the
actual market conditions encountered. The regime said "ranging" → scalp mode armed.
The scalp entry required a breakout signal that doesn't occur in a ranging market.
The strategy was self-defeating by construction.

Secondary issue: the dual-mode design violated Rule 10 (no duplicate subsystems). The
strategy had two independent signal paths that shared state in an undocumented way,
making the execution path non-deterministic for debugging.

## Gate Scorecard

| Check | Result |
|---|---|
| n ≥ 50 | **FAIL (n = 0 live, n = ~20 backtest only)** |
| All checks | Not evaluated (insufficient trades) |

**Verdict: REVERTED** (insufficient evidence — never traded in demo; conceptual flaw found)

## Lesson

A strategy that has never executed a single trade in 100 demo trading cycles has no evidence
of viability. "Works in backtest" is not evidence when the backtester used a different entry
trigger than the live system.

The dual-mode design also illustrates why one-implementation-per-concern matters: two signal
paths sharing state = two sources of the same bug.

## Prohibition

Archived per GROUND_TRUTH.md rule 2. Any "dual-mode v2 with fixed regime transition" is a
new trial. The conceptual flaw (regime filter + scalp entry are mutually exclusive) must be
resolved at the spec level before any code is written.
