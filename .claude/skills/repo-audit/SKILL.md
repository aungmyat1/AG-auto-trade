---
name: repo-audit
description: Audit repository architecture and hygiene against GROUND_TRUTH. Use when asked to analyze/audit the repo, check architecture, review project structure, or before merging structural changes.
---

# Repo Auditor

The old system died at 66,859 LOC with 7 duplicated subsystems and a DANGEROUS verdict.
This audit exists so that never happens again.

## Checks

1. **Build-order discipline** (GROUND_TRUTH.md): no alpha logic before the gate, no
   execution code before a ROBUST verdict. `ag/execution/` must stay empty until Phase 3.
   Anything violating the order is a critical finding.

2. **Duplicate-subsystem scan.** One implementation per concern. Specifically hunt the
   old repo's failure pairs: risk engines, circuit breakers, strategy trees
   (`strategies/` vs `strategy/`), orchestrators, exchange/data clients, resilience
   systems, paper/shadow environments. Two of anything = finding.

3. **LOC + sprawl.** `find ag scripts -name '*.py' | xargs wc -l | sort -rn`. Flag any
   file > 500 lines, any module that grew > 2x since last audit, and dead/empty packages.

4. **Locked-file integrity.** `git log --oneline -- ag/validation/lock_before_look/` —
   GATE_DECISION.md must have exactly its pre-registration history. Any later commit
   touching it is a critical finding. Thresholds in `gate.py`/`config.py` must still
   match the locked file.

5. **Secrets + boundary.** Scan tracked files for key material (same patterns as
   `.claude/hooks/bash_guard.py`); confirm `.env` is gitignored; confirm no broker/IB
   credentials or live-venue code in cloud-side modules.

6. **Test coverage honesty.** Map `tests/` against `ag/` modules; list modules with zero
   tests (known debt: risk engine, regime classifier). README claims must match reality.

7. **Docs freshness.** `docs/PROJECT_STATE.md` updated within the last meaningful change?
   `VALIDATION_STATUS.md` consistent with `research_archive/` contents?

## Output

Write `docs/audits/REPO_AUDIT_<YYYY-MM-DD>.md`: findings table (severity: CRITICAL /
WARN / INFO, with file:line evidence), KEEP/DELETE/REWRITE recommendations, and a
one-paragraph verdict. Update the Known Gaps table in `docs/PROJECT_STATE.md`.
Do not modify code during an audit.
