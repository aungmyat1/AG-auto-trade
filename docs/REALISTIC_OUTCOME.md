# AG Auto-Trade — Realistic Outcome Assessment

> Honest version. Built from the system's actual code and validation record, not generic optimism.
> Companion to `docs/ROADMAP.md`. Last updated: 2026-06-14.

## One-line summary

You are ~90% of the way to owning a **rigorous strategy-validation machine**. You are **0% of the
way to a proven profitable SMC bot** — because that question has not been answered yet, and the
evidence so far says *be skeptical*.

## What is actually built today (real, verifiable)

- A locked statistical **validation gate** (CPCV, walk-forward, Monte-Carlo, Deflated-Sharpe,
  net-of-cost) — pre-registered so thresholds can't be fudged after seeing data.
- A non-bypassable **6-guard risk engine** (0.5%/trade, 2% daily, 6% weekly, 15% max drawdown).
- **SMC detectors** (order block, FVG, BOS/ChoCH, liquidity sweep, displacement) — used as a
  *context filter only*, never as an entry signal.
- A **data layer** (Databento + Interactive Brokers loaders) — built, but the cache is empty;
  no real bars yet.
- **498 passing tests.** Platform phase complete.

This part is genuine and valuable regardless of whether SMC works.

## The question that is NOT yet answered

**Does SMC actually make money on gold futures (GC), net of costs, out of sample?**

No SMC strategy has been tested on this data yet. What we *do* have is prior evidence, and it is
not encouraging:

| Prior test | Result |
|---|---|
| SMC H1 (crypto) | **FRAGILE** — failed resampling (CPCV 0.92, Monte-Carlo 0.89) |
| SMC 5-minute (crypto) | **FAIL** — profit factor 0.08 |
| SMC on EURUSD / XAUUSD (H1, H4) | **FAIL** — PF 0.70–0.89 |
| Master-trader copy (A2) | **READ, not deployable** — looked great (PF 3.7) but failed the overfitting check (DSR z = −25) |

Every rigorous SMC test to date has either failed or been demoted. That is the honest prior.

## Realistic outcomes (informed estimate, not a guarantee)

When the first real gate runs on GC data, the most likely results are:

- **~65–75% — No robust edge** (FRAGILE/READ). You get a *validated "no"*: SMC doesn't survive on
  gold, and you learned it for the price of a backtest, not a blown account.
- **~20–30% — Marginal** (passes READ, fails ROBUST). Not deployable alone; might contribute to an
  ensemble.
- **~5–10% — Robust edge found.** Then: 30-day dry-run → 30-day shadow → tiny live pilot
  ($100 → $1,000). Even here, live performance is usually *thinner* than backtest.

These odds reflect (a) this project's own track record, (b) the base rate for retail SMC strategies,
and (c) a deliberately strict gate. They are not pessimism — they are the reason validation was
built first.

## Realistic timeline

- **First verdict:** days-to-weeks *after* data access is connected (currently the only blocker —
  needs the owner's Databento key or an IB session).
- **Any live trading (if something passes):** ~2–3 months minimum (dry-run + shadow + pilot ramp).
- **Multi-strategy platform / portfolio scanner / SaaS / AI quant:** 1–2+ years, and **contingent on
  first finding any edge at all.**

## What it will be — and won't be

**Will be:** a reusable, auditable trading *operating system* where SMC is the first plug-in
strategy, and a machine that tells you the truth about any future strategy idea cheaply.

**Will not be (near-term):** a money-printing bot, a guaranteed profit, a multi-exchange crypto
platform, or a SaaS business. Those require a proven edge that does not yet exist.

## The reframe that's actually true

The valuable asset here is **not "an SMC bot."** It's the **validation engine** — the thing that
will save you from deploying strategies that look good and lose money. If SMC fails the gate
(likely), that is the system *working*, not failing. The first profitable, *survivable* strategy you
ever run live — SMC or otherwise — will be worth more than ten that merely looked good in a backtest.

> **Most honest framing:** *"I'm building a machine that decides whether trading strategies are real.
> SMC is the first one it will judge. The probable answer is no — and that's a result worth having."*
