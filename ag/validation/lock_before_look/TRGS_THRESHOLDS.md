# TRGS PRE-REGISTERED THRESHOLDS
# Committed BEFORE any gate run. Do NOT modify after any alpha sees real data.
# Locked: 2026-06-14

## Purpose

The Trading Readiness Gate System (TRGS) is a DEPLOYMENT decision layer.
It sits on top of the ValidationGate (GATE_DECISION.md) and answers ONE question:
"Is the system safe to deploy capital?"

It does NOT replace the ValidationGate. Both must pass.

## Ladder Tiers

| Tier | Label | Minimum Requirements |
|------|-------|----------------------|
| 0 | NOT_READY | Gate not run, or FRAGILE verdict |
| 1 | READY_FOR_BACKTEST | Look-ahead tests PASS + RiskEngine tests PASS |
| 2 | READY_FOR_PAPER | Gate verdict = READ (n≥50, gross PF>1) AND edge beats random by ≥10% |
| 3 | READY_FOR_SHADOW | Gate verdict = ROBUST AND n≥500 AND max_dd<10% AND edge ≥10% |
| 4 | READY_FOR_LIVE | READY_FOR_SHADOW status AND manual_override = True (OWNER only) |
| — | BLOCKED | Any look-ahead violation OR replay integrity failure |

## TRGS-Specific Thresholds (additive on top of GATE_DECISION.md)

| Check | Tier Required | Value | Note |
|-------|---------------|-------|------|
| `n_trades` for shadow | READY_FOR_SHADOW | ≥ 500 | Stricter than gate ROBUST (200) |
| `max_drawdown` for shadow | READY_FOR_SHADOW | < 10% | Stricter than gate ROBUST (15%) |
| `edge_vs_random` | READY_FOR_PAPER+ | ≥ 10% outperformance | PF alpha ≥ 1.10 × random baseline PF |
| `daily_loss_limit` | Risk engine (all tiers) | ≤ 2% | Matches RiskEngine G1, unchanged |
| `live_override` | READY_FOR_LIVE only | True | Must be set explicitly by OWNER |

## Relationship to GATE_DECISION.md

GATE_DECISION.md thresholds are unchanged and still authoritative for the ROBUST verdict.
The TRGS adds ADDITIONAL requirements beyond ROBUST for shadow/live tier promotion.

An alpha that achieves ROBUST (n=200, DD=14%) reaches READY_FOR_PAPER but NOT
READY_FOR_SHADOW — it must accumulate more trades (n≥500) and reduce live DD below 10%.

## Rules

1. This file must not be modified after any alpha has been exposed to validation data.
2. TRGS thresholds are enforced in `ag/validation/readiness.py`. Do not hand-tune them.
3. manual_override = True requires explicit OWNER action — never set by the agent.
4. BLOCKED supersedes all tiers; no BLOCKED system may be promoted by any means.
