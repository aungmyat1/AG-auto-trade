# AG Auto-Trade — Success Criteria (promotion gates)

> Objective, emotion-free promotion gates. A strategy advances only when **every** criterion for
> the next state is met. Maps to the deployment states in `docs/ROADMAP.md`. Thresholds are the
> pre-registered, immutable gate (`ag/validation/lock_before_look/GATE_DECISION.md`) — they are not
> tunable, in either direction, after data exposure.

## Deployment states

```
NOT_READY → READY_FOR_PAPER → READY_FOR_SHADOW → READY_FOR_LIVE_PILOT → READY_FOR_SCALE
```

## The locked gate (the backtest bar)

```
n ≥ 200 net trades      net PF > 1.25        win rate > 45%
Sharpe > 1.2            max DD < 15%          CPCV median PF > 1.0
WF pass rate ≥ 60%      MC 5th-pct PF > 0.9   DSR z-score > 0     (all net of CME cost)
```
A strategy that meets **all nine** earns the **ROBUST** verdict. Meeting only the floor
(n ≥ 50, gross PF > 1.0) is **READ** — data exists, edge unproven. Anything less is **FRAGILE**.

## Promotion gates

| To state | Criteria (all required) |
|----------|--------------------------|
| **READY_FOR_PAPER** (dry-run) | Verification ladder rungs 0–6 green (architecture, code quality, component, integration, **no look-ahead / no repaint**, risk verified) **AND** a **ROBUST** gate verdict on GC, net of cost. |
| **READY_FOR_SHADOW** | 30-day paper / dry-run complete: no crashes, all 6 risk guards obeyed, realized expectancy tracks the backtest within tolerance (no material live-vs-backtest drift). |
| **READY_FOR_LIVE_PILOT** | 30-day shadow complete (production logic, virtual orders) with stable behavior **AND** infrastructure-resilience tests pass (API-down / DB-fail / reboot / outage → safe-mode + state recovery) **AND** explicit **owner authorization**. The owner flips the live flag manually — never the agent. |
| **READY_FOR_SCALE** | Live pilot ($100 → $1,000 ramp) shows results consistent with the validated edge over a meaningful sample (≥ ~100 live trades), no execution-cost surprises, and slippage/latency/capacity stay stable in 10k/50k/100k sims. |

## Demotion / correction

- A strategy that **fails any gate** routes through the Master Correction Loop
  (`ROADMAP.md`): root-cause → fix → unit → integration → replay → re-run the failed gate.
  Never skip forward to live testing.
- A **FRAGILE** result is archived to `research_archive/<alpha>/` with a verdict header.
  It is **not** tuned to "pass" — tuning a rejected entry to flatter it is forbidden
  (`GROUND_TRUTH.md`). Every parameter tried still counts toward `--n-trials`.

## Why this exists

To remove emotion and hindsight from go/no-go decisions: the criteria are fixed *before* results
are seen, so a strategy is promoted because it cleared an objective bar — not because it looked
promising on a particular chart.
