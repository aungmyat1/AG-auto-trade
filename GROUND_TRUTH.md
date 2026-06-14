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

| Alpha  | Status              | Verdict              | Notes |
|--------|---------------------|----------------------|-------|
| A0_MVP | TESTED 2026-06-14   | FRAGILE              | 38 trades < n≥50 floor; sweep+ChoCH plumbing check; gate skipped; archived `research_archive/a0_mvp/` |
| A1 (full WHERE+WHEN) | NOT BUILT | SPEC LOCKED | §1 requires ≥3-of-4 WHERE confluence + ≥2-of-3 WHEN; **WHEN never implemented**. Do not wire+gate on seen 2020-24 data. `A1_SMC_MOMENTUM_DECISION.md` |
| A1_WHERE_ONLY | TESTED 2026-06-14 | **UNSCOREABLE** | sweep+ChoCH+OB+FVG+displacement (no WHEN, no Fib); GC 5yr n=33<50 (WR 66.7%); archived sweep+ChoCH→entry pattern, FRAGILE-expected. `A1_WHERE_ONLY_DECISION.md` |
| A2     | TESTED 2026-06-12   | READ (OPTIMISTIC)    | n=325 OOS, net PF=3.745, 10/11 pass, DSR z=−25.32 |
| A3     | NOT TESTED          | PENDING              | Ensemble; spec locked + skeleton built |

## Build Order (v4)

1. Validation core (plain Python, zero engine dependency) ✅ 2026-06-12
2. Platform (risk, regime, monitoring, infrastructure) ✅ 2026-06-13 (G5 fixed; 392 tests green; env loader; monitoring = Telegram stub; data/ empty pending Phase B)
3. Alpha modules (A1, A2, A3 to common AlphaModule interface) ← CURRENT
4. Gate race (A1 vs A2 vs A3 — cloud MAIN, compute-heavy)
5. Execution (Nautilus L3 + IB) — only if a ROBUST alpha exists
