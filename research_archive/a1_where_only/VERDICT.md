# A1_WHERE_ONLY — VALIDATED-NEGATIVE (UNSCOREABLE)

**Verdict:** UNSCOREABLE — n=33 on GC 5yr (2020–2024). **Not re-run.**
**Closed:** 2026-06-14
**Pattern:** sweep + ChoCH/BOS + OB + FVG + displacement → entry. **No WHEN trigger, no Fib.**

This is the **third non-pass of WHERE-only SMC-as-entry**:
- crypto-SMC H1 — **FRAGILE** (`research_archive/legacy_smc_failures/SMC_H1_FRAGILE.md`)
- A0_MVP (sweep+ChoCH) — **FRAGILE** (`research_archive/a0_mvp/`)
- A1_WHERE_ONLY (this) — **UNSCOREABLE** (n<50 on a full 5-year window)

Per GROUND_TRUTH §7 / CLAUDE.md rule 3: never re-promoted, never quietly re-tested. The locked
full-A1 (WHERE+WHEN) remains SPEC LOCKED, **NOT BUILT** (`A1_SMC_MOMENTUM_DECISION.md` §1 untouched).
Spec lock for what ran: `ag/validation/lock_before_look/A1_WHERE_ONLY_DECISION.md` (floor 14+6=20).

## Result
| Instrument | Signals | Approved (n) | Band | Notes |
|---|---|---|---|---|
| GC 1h 2020–2024 | 50 | **33** | UNSCOREABLE (n<50) | WR 66.7%, mean R +0.059 — quality promising, frequency fatal |
| 6E 1h 2020–2024 | 282 | 3 | ARTIFACT | risk-engine state-locked from 2020 COVID volatility — not a valid count |

## Why n=33 — code-level diagnosis (most likely cause)
**(b) over-strict filter**, not (a) genuine rarity or (c) a detector bug:
- **AND-gating of all five WHERE components** (`a1_alpha.py:91-119`) — sweep AND struct-break
  AND OB AND FVG AND displacement, every one required. The spec intended **≥3-of-4 confluence**;
  the build requires **all 5**. AND-gating 5 components is vastly more selective than 3-of-4 of 4.
- Compounded by the **displacement ≥1.8×ATR** requirement (a genuinely rare strong-momentum
  candle) being a hard AND-gate, not one vote among several.
- The multi-OB tracker is correct (`a1_alpha.py:52,79` — accumulates, not single-latest) → **not**
  the legacy `_last_zone_ffill` under-firing bug. Thresholds are ATR-relative (not absolute) → not
  the legacy `min_atr=20`-style cull.

**Implication:** the WHERE-only-SMC-as-entry *question* was not fairly answered by this artifact —
the AND-gating starved it. A spec-conformant **≥k-of-n confluence** would be a **new alpha** (new
ID, pre-registered, gated on a FRESH unseen window), distinct from this archived artifact. To be
confirmed empirically by the funnel measurement (`docs/dispatch/A1_FUNNEL_DIAGNOSIS.md`). This does
not authorize loosening: the redesign decision is the owner's (build-WHERE-redesign vs promote-A2).
