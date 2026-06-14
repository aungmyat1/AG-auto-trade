# REJECTED — ROADMAP v5 (Bybit SMC pivot)

**Status:** REJECTED ON CORRECTED FACTS · 2026-06-14
**Decision by:** owner
**Proposal:** switch the venue from CME futures (GC/MGC/6E via IBKR/Databento/Nautilus) to
Bybit crypto perpetuals (BTC/USDT H1) via Freqtrade + pybit. Preserved here per the
never-delete rule; do not re-propose without new evidence.

## Why rejected

The proposal kept the validation-first spine (good), but its load-bearing justifications did
not hold against the actual `AG-auto-trade` repo:

1. **"Reuse your existing Bybit/Freqtrade config" — FALSE here.** `smc-config.json`, `app/`,
   `freqtrade`, `user_data`, and any `ccxt`/`pybit`/Freqtrade code are **absent** from this
   repo (they live in the old `auto-trade-system`). In this repo Bybit+Freqtrade is a
   **from-scratch build**, not a reuse — the "fastest path" advantage evaporates.

2. **"GoldTrendFollowing v2 is a validated ROBUST fallback (PF 1.765)" — FALSE.** The repo's
   honest re-validation (`docs/validation/GOLDTF_REVALIDATION.md`) verdict is **FRAGILE**: the
   1.765/2.441 figures were in-sample / DB-engine; the honest **OOS** result is
   **PF 1.017, Sharpe 0.235, return −5.93%, n=47** — it failed the gate. There is no working
   safety net (and it is a Gold strategy — it would not transfer to Bybit BTC anyway).

3. **"BTC H1 is the only timeframe that ever passed a gate" — overstated.** BTC H1 passed
   Gate-1 mechanically but was **FRAGILE** (CPCV 0.9157 FAIL, MC p5 0.889 FAIL, t-stat 0.31).
   The pivot's anchor rests on a result the robustness gate rejected.

4. **Locked-rule conflicts:** reverses GROUND_TRUTH's locked futures venue, and violates the
   active freeze (Rule 2 — no BTC/ETH work before the first real GC verdict).

## Owner's standing decision

> Proceed with A1 on GC. There is no validated strategy on any venue yet — which is precisely
> why the GC gate race must run before any venue is reconsidered. The only thing that re-opens
> the venue question is evidence: GC A1/A2/A3 all FRAGILE or uneconomic. Even then, crypto-SMC's
> own FRAGILE verdict means Bybit-SMC is not the obvious successor.

## What was kept from v5 (already true in the repo, venue-independent)

The locked intraday gate (PF>1.25 net, n≥200, Sharpe>1.2, +CPCV/WF/MC/DSR), SMC-as-filter,
the unfiltered-baseline comparison, and "SMC may fail without killing the project." These are
already the design and do not depend on the venue.
