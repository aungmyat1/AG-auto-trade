# GROUND TRUTH — AG Auto Trade

**Repo status:** CLEAN FOUNDATION (v4 fresh start)
**Date initialized:** 2026-06-12
**Source archive:** auto-trade-system (DANGEROUS verdict, 2026-05-28 audit)

## Architecture Decisions (locked)

1. Validation core is built FIRST — the gate is the asset, not any strategy.
2. Three alphas race identically (A1/A2/A3) — no primacy by assertion.
3. SMC = context filter only (already FRAGILE from crypto). Never generates entries.
4. Futures target: GC/MGC + 6E via Databento + IB + Nautilus (Phase 3).
5. Cloud MAIN = research/validation (no keys). VPS WORKER = execution (owns keys).
6. Goalposts locked in git (validation/lock_before_look/GATE_DECISION.md) before data exposure.

## Alpha Verdicts

| Alpha | Status       | Notes |
|-------|-------------|-------|
| A1    | NOT TESTED  | SMC-filter + momentum/delta — detectors built, spec locked 2026-06-12 (gate run blocked pending data) |
| A2    | READ (OPTIMISTIC) | Master-trader copy (SignalStart) — gated 2026-06-12; DSR fails (z=−25.32); not ROBUST, ensemble input only |
| A3    | NOT TESTED  | Ensemble |

## Build Order (v4)

1. Validation core (plain Python, zero engine dependency) ✅ 2026-06-12
2. Platform (risk, regime, monitoring, infrastructure) 🟡 2026-06-12 (risk/regime tests delivered; monitoring = Telegram stub; infrastructure/ + data/ empty)
3. Alpha modules (A1, A2, A3 to common generate_signal() interface) ← CURRENT
4. Gate race (A1 vs A2 vs A3 — cloud MAIN, compute-heavy)
5. Execution (Nautilus L3 + IB) — only if a ROBUST alpha exists
