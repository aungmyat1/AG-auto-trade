# RESEARCH ARCHIVE — M15 Fee Trap
# Verdict: FAIL (gross-negative)
# Date archived: 2026-06-12
# DO NOT RE-TEST. Validated negative result.

---

## Strategy Description

M15 (15-minute bar) scalping strategy applied to three instruments:
- XAUUSD (spot gold)
- BTC/USDT perpetual
- ETH/USDT perpetual

Signal logic: momentum/breakout on 15-minute closes with tight stops.

## Why It Failed

**Fee trap**: At 15-minute resolution the average gross R per trade is approximately equal to
the round-trip commission + spread + slippage (0.10–0.15% per leg on crypto perps). A strategy
that is marginally profitable gross becomes gross-negative net of cost at this timeframe
before any edge erosion from execution.

The strategy was gross-negative across all three instruments — meaning it failed BEFORE the
cost model was applied. The winning signals did not cover the losing signals even without fees.

## Gate Scorecard

| Check | Result |
|---|---|
| n ≥ 50 | PASS (sufficient trades per instrument) |
| gross PF > 1.0 | **FAIL — all 3 instruments gross PF < 1.0** |
| All ROBUST checks | Not evaluated (floor failed) |

**Verdict: FRAGILE** (gate floor failed — gross-negative)

## Lesson

The 15-minute timeframe for futures-style momentum is a fee trap for retail instruments.
Fee floor requires minimum spacing of ~0.40% (per Pionex grid research, consistent across contexts).
At M15 the average move captured is well below this floor.

**Do not re-test M15 breakout/momentum on crypto spot or perp without first verifying that
average gross R per trade (before costs) materially exceeds 0.15% per leg.**

## Prohibition

This result is archived, not deleted. Per GROUND_TRUTH.md rule 2:
"FRAGILE → research_archive/ with verdict header; never deleted, never quietly re-tested."

Any proposal to "try M15 again with different parameters" must be treated as a new trial
(+1 to n_trials in DSR calculation) and requires a lock-before-look spec committed first.
