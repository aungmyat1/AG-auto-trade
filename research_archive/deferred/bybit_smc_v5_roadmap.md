# Deferred: Bybit SMC Trading Bot (ROADMAP v5)

**Status:** DEFERRED — not deleted. Pre-registered contingency, not an active plan.

## Activation trigger (pre-committed, evidence-gated)

ACTIVATE ONLY IF one of these conditions is met and confirmed by the owner:

1. GC A0_MVP **and** A1 both return FRAGILE on real Databento data; OR
2. GC/6E data + execution costs prove uneconomic for a solo operator after a real verdict.

Until one of those conditions is true, this roadmap is frozen.
The pivot rule is decided here, before the verdict — so the verdict triggers it, not mood.

## What this roadmap proposes

A Bybit perpetuals SMC bot running on Freqtrade, primary instrument BTC/USDT:USDT H1.
SMC as a context filter (LONG_ALLOWED / SHORT_ALLOWED / NO_TRADE), momentum trigger for entry.
Monetization ladder: Bybit Master Trader → signal SaaS → PAMM/MAM.

## Why it's deferred, not deleted

- BTC H1 SMC returned FRAGILE previously (PF 1.137). No new evidence changes that yet.
- The current project (GC gate race) is days from a first verdict once the Databento key lands.
- Rule 2 (ROADMAP.md): no BTC/ETH infrastructure before first GC/6E verdict.
- Pivoting on impatience, not evidence, is exactly what the gate apparatus exists to prevent.

## If activation triggers

The full v5 spec lives in the original document shared 2026-06-14. Key decisions:
- Lock H1 as primary timeframe (5m and M15 both FAIL per prior research).
- Bybit intraday gate: PF >1.25 net, Sharpe >1.2, MaxDD <15%, n ≥200, DSR >0.
- SMC must beat unfiltered baseline net OOS — earns primacy by evidence, not assertion.
- GoldTrendFollowingStrategy v2 (PF 1.765, Sharpe 1.42) races as the validated fallback.
- Cloud MAIN: research/validation only, no keys. VPS WORKER: owns keys, only thing that trades.

## Open questions at activation time

1. Does Bybit list XAU/USDT:USDT perp? If yes, joins the race. If no, BTC-only.
2. Forex via Bybit needs MetaTrader 5 / MetaApi — confirmed deferred to Upgrade 3.
3. Archive the old `auto-trade-system` demo trade log before starting fresh.
