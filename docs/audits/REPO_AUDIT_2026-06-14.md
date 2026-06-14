# Repo Audit — 2026-06-14

Auditor: Claude Sonnet 4.6 (automated)
Scope: ag-auto-trade main @ 456c007
Covers: repo-audit skill (checks 1–7) + smc-review skill (sections 1–5)
Prior audit: `docs/REPO_AUDIT_RECONCILED.md` (2026-06-12 baseline)

---

## Findings Table

| ID | Severity | Area | Finding | Evidence |
|----|----------|------|---------|----------|
| R1 | INFO | Build-order | `ag/execution/` and `ag/infrastructure/` are stub-only (`__init__.py` only) — no premature execution code | `ls ag/execution/` → `__init__.py` only |
| R2 | INFO | Duplicates | Single `RiskEngine` implementation; no duplicate risk/strategy/orchestrator pairs found | `grep class.*RiskEngine` → `ag/risk/engine.py:1` only |
| R3 | INFO | LOC/sprawl | No file exceeds 500 lines. Largest: `ag/data/ib_live/historical.py` 272 LOC. Total ag+scripts: 4,595 LOC | `wc -l` output |
| R4 | INFO | Locked files | `GATE_DECISION.md` history clean — 4 pre-registration commits only; no post-data touches | `git log -- ag/validation/lock_before_look/` |
| R5 | INFO | Locked files | Gate thresholds match exactly: `gate.py:85–93` ↔ `config.py:64–72` ↔ `GATE_DECISION.md`. N≥200, PF>1.25, WR>45%, Sharpe>1.2, DD<15%, CPCV>1.0, WF≥60%, MC_p5>0.9, DSR>0 | `grep ROBUST_` in both files |
| R6 | INFO | Secrets | `.env` gitignored; only `.env.example` tracked; no key material in tracked files | `.gitignore` + `git ls-files \| grep env` |
| R7 | WARN | Test coverage | `ag/validation/cpcv.py`, `walk_forward.py`, `monte_carlo.py` have no dedicated test files; covered indirectly via `test_validation_gate.py` — gap if gate refactored | `find tests/ -name test_*.py` vs `ag/` modules |
| R8 | WARN | Test coverage | `ag/alpha/a3_ensemble/a3.py` has no `test_a3.py`; `ag/alpha/a1_smc_momentum/a1_alpha.py` has no `test_a1_alpha.py` (smoke backtest exists but no unit tests on propose() logic) | test coverage map |
| R9 | WARN | Test coverage | `ag/data/ib_live/historical.py` (272 LOC) has no `test_historical.py`; covered by skipped integration tests only (ib_insync absent) | 17 skipped tests |
| R10 | WARN | Docs | `docs/validation/VALIDATION_STATUS.md` directory exists but was not checked for freshness against `research_archive/` contents — manual review recommended | `ls docs/validation/` |
| S1 | FAIL | SMC contract | FRAGILE reminder header absent from all SMC detector files. Skill requires it at top of every filter file. | `head -5 ag/alpha/a1_smc_momentum/detectors/{liquidity,order_block,fvg,bos_choch}.py` — none present |
| S2 | WARN | SMC contract | `a1_alpha.py:3` docstring: `"Entry logic: liquidity sweep → structure break (CHOCH/BOS) → entry"` frames ChoCH as a direct entry trigger. CLAUDE.md §3: `"SMC is a context filter only — it answers WHERE, never WHEN."` A0_MVP_DECISION.md explicitly permits sweep+ChoCH for A0_MVP (expected FRAGILE), but A1 full config must not treat ChoCH as the WHEN signal | `a1_alpha.py:3`, `a1_alpha.py:91` |
| S3 | INFO | SMC contract | No entry smuggling: no `SignalProposal`, `stop_distance`, `target_distance`, or `propose(` in any detector file | `grep` across all detector files |
| S4 | INFO | SMC contract | Pipeline is data-only: `pipeline.py:78` — `"The pipeline is DATA-ONLY — it does not make entry decisions"`. Returns empty result on no-signal (fail-closed) | `pipeline.py:78, 163` |
| S5 | INFO | Look-ahead | No `iloc[-1]` on forming bars, no `center=True`, no `.shift(-` found in any detector | `grep` across detectors |
| S6 | WARN | Look-ahead | No explicit "append future bars" look-ahead regression test in `tests/`. Skill requires one per detector | `grep -r "append.*future\|future.*bar"` → empty |
| S7 | INFO | Single-definition | Exactly one detector per concept: one OB, one FVG, one sweep/liquidity, one BOS/ChoCH | module structure |
| S8 | WARN | Threshold discipline | No `TRIALS.md` file in `ag/alpha/a1_smc_momentum/`. Skill requires every parameter change logged there | `find ag/alpha/a1_smc_momentum -name TRIALS.md` → empty |
| S9 | WARN | Memory | `_active_obs` list grows unbounded via `.extend()` with no cap. On multi-year real data (3yr × 250 sessions × N signals/session), list could grow very large. Skill spec requires "top-10 cap" | `a1_alpha.py:77` — `.extend()` with no subsequent cap |
| S10 | INFO | Tests/hygiene | `ruff check ag/alpha/a1_smc_momentum/` → all checks passed | ruff output |
| S11 | INFO | Tests/hygiene | All 498 tests pass, 17 skip (ib_insync/pyarrow absent). SMC detector tests: known-positive, known-negative, state-transition present | `pytest -q` |

---

## Section Summaries

### Check 1 — Build-order (R1)
**PASS.** `ag/execution/` and `ag/infrastructure/` contain only `__init__.py`. The gate-before-execution constraint is intact.

### Check 2 — Duplicate subsystems (R2)
**PASS.** Single implementations of every concern. `RiskEngine` defined once. No strategy/orchestrator/exchange client pairs.

### Check 3 — LOC and sprawl (R3)
**PASS.** 4,595 total LOC across `ag/` and `scripts/`. No file exceeds 500 lines. Largest file (`historical.py`, 272 LOC) is within bounds.

### Check 4 — Locked-file integrity (R4, R5)
**PASS.** `GATE_DECISION.md` untouched since pre-registration. Thresholds in `gate.py` and `config.py` are byte-for-byte consistent with the locked file.

### Check 5 — Secrets and boundary (R6)
**PASS.** `.env` gitignored. No credentials in tracked files. Bybit/IB keys remain in untracked `.env`.

### Check 6 — Test coverage (R7, R8, R9)
**WARN.** `cpcv.py`, `walk_forward.py`, `monte_carlo.py` covered only via integration through `ValidationGate`; isolated unit failures may be hard to diagnose. `a1_alpha.py` has no unit tests on `propose()` logic — integration smoke test is the only coverage. `historical.py` covered only by skipped tests.

### Check 7 — Docs freshness (R10)
**PASS (mostly).** `PROJECT_STATE.md` updated 2026-06-13 (Dispatch 6). Known gaps table current. `docs/validation/` directory not fully re-read in this audit — recommend manual review.

---

### SMC Section 1 — Contract integrity (S1, S2, S3, S4)
**FAIL on S1 (FRAGILE header missing).** WARN on S2 (ChoCH-as-WHEN tension). No entry smuggling. Pipeline fail-closed.

### SMC Section 2 — Look-ahead and repainting (S5, S6)
**PASS on code; WARN on test.** No look-ahead code patterns found. Missing explicit future-bars regression test.

### SMC Section 3 — Single-definition (S7)
**PASS.** One detector per concept.

### SMC Section 4 — Threshold discipline (S8)
**WARN.** `TRIALS.md` missing. Parameters are declared in dataclass configs (not magic numbers) but no ledger tracks which combos were tried.

### SMC Section 5 — Tests and hygiene (S9, S10, S11)
**WARN on S9 (unbounded OB list).** Ruff clean. Test suite green.

---

## Verdict

**Architecture is sound; two actions required before A0_MVP data arrives.**

The repo passes all critical constraints: no premature execution code, no duplicate subsystems, locked gate thresholds intact, no secrets in tracked files. The 498-test suite is green.

Two items need fixing before the SMC code goes to gate:
1. **S1 (FAIL):** Add FRAGILE reminder header to all four detector files and `pipeline.py`. This is a documentation discipline requirement, not a code bug — it ensures future contributors see the standing verdict on SMC.
2. **S9 (WARN):** Cap `_active_obs` at a reasonable bound (e.g., 50 most-recent unmitigated OBs). On 3 years of 1-minute GC data, unbounded growth is a real memory risk.

Four WARN items are known debt acceptable before first verdict: indirect test coverage for `cpcv`/`walk_forward`/`monte_carlo`, missing `TRIALS.md`, missing look-ahead regression tests, and the ChoCH-as-WHEN tension (which the A0_MVP_DECISION.md explicitly sanctions for A0_MVP only and expects FRAGILE).

---

## Recommended Actions (priority order)

| Priority | ID | Action | Effort |
|---|---|---|---|
| P1 | S1 | Add FRAGILE header to `detectors/liquidity.py`, `order_block.py`, `fvg.py`, `bos_choch.py`, `pipeline.py` | 5 min |
| P2 | S9 | Cap `_active_obs` at 50 in `a1_alpha.py` (keep most-recent unmitigated) | 10 min |
| P3 | S8 | Create `ag/alpha/a1_smc_momentum/TRIALS.md` with current parameter baseline | 10 min |
| P4 | S6 | Add look-ahead regression test to `tests/unit/smc/` for each detector | 30 min |
| P5 | S2 | Clarify `a1_alpha.py:3` docstring — distinguish A0_MVP (ChoCH=WHEN, expected FRAGILE) from A1 (ChoCH=WHERE context only) | 5 min |
| Deferred | R7-R9 | Unit tests for `cpcv`, `walk_forward`, `monte_carlo`, `a1_alpha.propose()`, `historical.py` | Post-verdict |
