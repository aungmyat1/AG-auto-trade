# PROJECT STATE — live memory (read me first, keep me updated)

Last updated: 2026-06-12

## Current Stage

**Platform built, alphas not started.** v4 build order position:

1. ✅ Validation core (gate, CPCV, purged WF, Monte Carlo, DSR, cost model) — 21 tests green
2. 🟡 Platform — risk engine + regime classifier implemented but **untested**; monitoring =
   Telegram stub; infrastructure/ + data/ empty
3. ⬜ Alpha modules A1 / A2 / A3 ← **CURRENT GOAL**
4. ⬜ Gate race (identical gate, all three alphas)
5. ⬜ Execution (Nautilus + IB) — forbidden until a ROBUST verdict exists

## Active Validation Target

- Instruments: GC (primary), MGC, 6E — per-instrument models, never shared
- Gate: `ag/validation/lock_before_look/GATE_DECISION.md` (locked 2026-06-12, immutable)
- Status of alphas: A1 NOT TESTED · A2 NOT TESTED · A3 NOT TESTED (`VALIDATION_STATUS.md`)
- Live trading: **OFF** (no ROBUST verdict exists; nothing may trade)

## Last Validation Evidence

- 2026-06-12: full test suite 21/21 green (cost model, deflated Sharpe, gate)
- No alpha has ever been gate-raced in this repo

## Known Gaps (carry-over from 2026-06-12 status review)

| Gap | Action |
|---|---|
| ~~Branch protection OFF on `main`~~ | ✅ Closed 2026-06-12 — owner enabled protection (require PR + checks, no force push) |
| ~~No CI~~ | ✅ Closed 2026-06-12 — `.github/workflows/ci.yml` on main; first run red until the build-backend fix (PR #1 or PR #2) merges |
| Lock-before-look loader missing | Gate thresholds hardcoded in `gate.py`/`config.py`; no code reads GATE_DECISION.md. Build with alphas. |
| Risk engine + regime classifier have zero tests | Write before alphas depend on them |
| Risk G5 leverage guard is a no-op (`ag/risk/engine.py` — comment says "enforced at execution layer", so `validate_entry()` never checks leverage) | Implement `leverage` param + test (plan Phase A2) |
| research_archive half-seeded | M15 fee-trap, ALiVMassit, dual-mode scalper rows lack record files |
| CPCV/WF train-side purge is a no-op | By design today (no per-fold refit on a static trade series; test-side purge IS applied). Revisit if fold-wise fitting is ever added. |
| ~~`ag/validation/cost_models/` empty dup~~ | ✅ Closed 2026-06-12 — empty package deleted |

## Next Goal

Execute `docs/IMPLEMENTATION_PLAN.md` (2026-06-12): Phase A platform hardening (risk/regime
tests, G5 fix, lock-before-look consistency test) → Phase B Databento GC/6E loader → then
A1 (SMC-filter + momentum/delta), A2 (master-trader copy), A3 (ensemble) against
`ag/alpha/base.py::AlphaModule`, with tests, logging every threshold tried (DSR trial count).
Then race all three through the gate on Databento GC history.

## Update Protocol

Any session that changes stage, verdicts, gaps, or goals must update this file in the same
commit. Stale memory is worse than no memory.
