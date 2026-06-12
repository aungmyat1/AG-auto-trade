# PRE-REGISTERED GATE DECISION — A3_ENSEMBLE
# Committed BEFORE any alpha sees data. Do NOT modify thresholds after data exposure.
# Locked: 2026-06-12

## Alpha Identity

**Alpha ID**: A3
**Description**: Ensemble of A1 (SMC-filter+momentum) + regime classifier + A2 (master-trader)
**Status at lock time**: Component alphas A1 and A2 not yet ROBUST.
  A3 may not be gated until both components produce confidence outputs.

## Signal Definition

A trade signal fires when the weighted ensemble score exceeds the threshold:

```
score = 0.4 * a1_confidence + 0.3 * regime_score + 0.3 * a2_confidence
fire if score > 0.75
```

**Weights are locked. They must not be tuned after any gate run.**
Each weight tuning attempt adds 1 trial to --n-trials.

### Component definitions

- **a1_confidence** (0.0–1.0): from `A1SmcMomentum.propose()` → `SignalProposal.confidence`
- **regime_score** (0.0–1.0): derived from `RegimeClassifier.classify()` → mapped per `_regime_to_score()`
  - EXPANSION = 0.85 base; NORMAL = 0.65; COMPRESSION = 0.40; CHOP = 0.20
  - EMA50 slope alignment bonus: +0.10 when slope direction matches trade direction
  - Score scaled by `size_multiplier` from regime result
- **a2_confidence** (0.0–1.0): from `A2MasterTrader.propose()` → `SignalProposal.confidence`

Conflicting A1/A2 direction → no signal (safety gate; not tunable).

## Entry / Exit Model

Inherited from the firing component with the higher confidence:
- **Stop**: 0.5% from entry (same as A1/A2)
- **Target**: 1.0% from entry (R:R = 2.0)
- **Position size**: 0.5% of account (G4 hard cap)
- **Risk engine**: `RiskEngine.validate_entry()` called on every signal; no bypass

## Instruments and Data

Same as A1 and A2: GC (primary), MGC, 6E — per-instrument, no cross-instrument model.

## Cost Model

`CostModel.for_gc()` — same as all other alphas. Net-of-cost PF only.

## Build Order Gate

A3 must NOT be gated until:
1. A1 has produced at least a READ verdict on GC data
2. A2 has produced at least a READ verdict (current: READ, 2026-06-12)
3. A3's signal series has n ≥ 50 trades on GC IS data (READ floor)

A3 being gated before A1 is gated would mean it inherits A1's confidence of 0.0
for all signals — equivalent to a 2-component ensemble, which is a different alpha.

## Gate Thresholds

IDENTICAL to `GATE_DECISION.md`:

| Dimension          | Floor (read) | ROBUST (capital required) |
|--------------------|-------------|---------------------------|
| Trades (n)         | >= 50        | >= 200                    |
| Profit factor      | > 1.0 gross  | > 1.25 NET of realistic cost |
| Win rate           | —            | > 45%                     |
| Sharpe             | —            | > 1.2                     |
| Max drawdown       | —            | < 15%                     |
| CPCV median PF     | —            | > 1.0                     |
| Purged WF folds    | —            | >= 60% with PF > 1        |
| MC 5th-pct PF      | —            | > 0.9                     |
| Deflated Sharpe    | —            | > 0                       |

## Trial Count (--n-trials)

- Base: 1 (this spec defines one fixed ensemble with locked weights)
- Each weight adjustment after IS data exposure: +1
- Each threshold adjustment (0.75 → other): +1
- Each regime scoring change: +1
- Log ALL in `ag/validation/trial_log.py`

## Rules

1. This file must not be modified after the first A3 gate run on GC data.
2. Weights (0.4/0.3/0.3) and threshold (0.75) are immutable after locking.
3. A3 does not get primacy over A1/A2 by assertion — all three race the identical gate.
4. If A3 is FRAGILE, archive to `research_archive/a3_ensemble/`. Do not relax weights.
