---
name: trading-research
description: Review a strategy idea or results for weaknesses and overfitting; recommend tests. Use when reviewing strategy proposals, analyzing backtest results, or asked "why did this fail" / "is this edge real".
---

# Trading Researcher

Research only — this skill never changes code and never proposes threshold changes to the
gate. Its job is to find the flaw before capital does.

## Before anything: check the graveyard

Read `research_archive/` and `VALIDATION_STATUS.md`. If the "new" idea is a re-skin of an
archived failure, say so immediately and cite the record. Known tuition already paid:

- **SMC-as-entry** — FRAGILE (crypto H1: CPCV median PF 0.92, MC 5th-pct 0.89) and
  gross-negative (5m sniper). SMC may only filter WHERE, never trigger WHEN.
- **High win rate ≠ edge** — ALiVMassit: 82.7% WR with 0.14 PF. Always ask for PF and
  R-distribution, never accept WR alone.
- **Fee trap** — M15 scalping went gross-negative across 3 instruments once real costs
  applied. Any low-timeframe idea must show net-of-cost expectancy per trade vs. the
  CME cost stack before deeper work.

## Overfitting review checklist

1. **Trial count honesty.** How many variants/thresholds were tried, including abandoned
   ones? That number feeds Deflated Sharpe. "We tuned it until it worked" = the finding.
2. **Per-instrument integrity.** One model per instrument (GC ≠ 6E). Shared parameters
   across instruments must be justified, not convenient.
3. **Data hygiene.** Look-ahead (signal uses bar close it couldn't know), survivorship
   (A2: dead SignalStart traders included?), regime coverage (does the sample include
   chop AND trend, news weeks, both sessions?).
4. **Sample size vs. claim.** n < 50: anecdote. n < 200: floor-read only. Confidence
   language must match n.
5. **Costs + slippage realism.** Limit-fill assumptions, spread at session edges,
   slippage on stop-outs. A2 specifically: copy-latency slippage.
6. **Fragility probes to recommend:** parameter ±20% sensitivity, walk-forward fold
   stability, Monte Carlo reshuffle, costs ×1.5 stress, regime-sliced PF.

## Output

A short memo: (a) verdict — pursue / fix-first / archive-now, (b) the single weakest
assumption, (c) the exact tests to run next with expected-if-real vs expected-if-overfit
outcomes, (d) the honest trial count to carry into `/backtest`. Recommend the
strategy-validator skill for the formal gate run.
