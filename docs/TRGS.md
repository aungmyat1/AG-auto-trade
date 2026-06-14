# Trading Readiness Gate System (TRGS)

> One question, fail-closed: **may this system risk real money right now?**
> A capital-deployment firewall — not a strategy. Code: `ag/readiness/`. Run:
> `python3 scripts/run_readiness_gate.py` (exit 0 only if cleared for live).

## What it is

TRGS **composes** the locked subsystems into one decision (it does not reimplement
them — GROUND_TRUTH rule 10):

| Validator | Composes | PASS means |
|-----------|----------|------------|
| `backtest` | locked `ValidationGate` | verdict == **ROBUST** (full battery, net-of-cost) |
| `replay` | `ag.validation.replay_harness` | no look-ahead, no repainting on the detectors |
| `risk` | locked `RiskEngine` | all 6 guards fire on the locked limits |
| `edge` | trade series | alpha beats a baseline by ≥ 10%, positive expectancy |
| `system_health` | Phase-D execution layer | API/order/DB/journal/dup-order/kill-switch healthy |
| `infra` | Phase-D execution layer | survives restart / API-fail / net-drop / delay |

The **decision engine** is fail-closed: any hard FAIL ⇒ `BLOCKED`; readiness is
earned, never defaulted. States: `NOT_READY → READY_FOR_BACKTEST → READY_FOR_PAPER
→ READY_FOR_SHADOW → READY_FOR_LIVE`, plus `BLOCKED`. `READY_FOR_LIVE` additionally
requires an explicit owner override — and **the engine never enables live trading**;
`LIVE_TRADING` stays an owner-only manual flip (hard rule 1).

## Reconciliations vs the TRGS design doc (locked rules win)

The submitted spec was adopted in structure but corrected where it conflicted with
pre-registered locked decisions:

1. **Backtest bar = the locked gate**, not "PF≥1.25 / WR>40% / 500 trades" alone.
   The locked gate is stricter and multi-dimensional (adds Sharpe>1.2, CPCV, WF,
   Monte-Carlo, Deflated-Sharpe; WR>45%). Using the looser single-PF bar would
   defeat the gate. `backtest_validator` requires the gate's ROBUST verdict.
2. **Risk limits = locked**: 0.5%/trade, **2%** daily (not 3%), 6% weekly, **15%**
   max DD (not 10%), ≤5× leverage, ≤3 concurrent.
3. **system_health / infra = NOT_AVAILABLE** until the Phase-D execution layer is
   built (locked until a ROBUST verdict). They fail closed — you cannot health-check
   a venue that does not exist — which correctly caps readiness below LIVE.
4. **Location `ag/readiness/`** (not `src/gate/`); reports via `ReadinessReport.to_json()`.

## Status today

Running it now returns **READY_FOR_BACKTEST** — the harness is *verified* (replay clean
after the LF-1 fix, all six risk guards fire) but it is NOT cleared for capital:
- `replay` **PASS** — all five SMC detectors are look-ahead- and repaint-clean (LF-1, the
  liquidity future-cluster look-ahead, was found by this suite and is now fixed).
- `backtest` NOT_RUN — no ROBUST verdict exists (no real GC data yet).
- `edge` NOT_RUN — no alpha-vs-baseline comparison yet.
- `system_health` / `infra` NOT_AVAILABLE — execution layer locked.

The firewall now says "your validation harness is trustworthy — go get a verdict," and it
will refuse LIVE until a strategy earns ROBUST on real GC data, the execution layer is
built, and the owner flips the switch. (Earlier it returned BLOCKED because the replay gate
caught LF-1 — that was the firewall working; the bug is now fixed.)
