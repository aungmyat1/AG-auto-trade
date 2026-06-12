---
description: GO/NO-GO checklist for any deployment step (dry-run or live). Default answer is NO-GO.
---

Run the deployment gate checklist. Every item needs cited evidence (file, line, date);
an unverifiable item is a FAIL. Default verdict is **NO-GO** — deployment must earn GO.

1. ROBUST verdict recorded in `VALIDATION_STATUS.md` for the candidate alpha
   (n ≥ 200, net PF > 1.25, full robustness battery intact) — cite the gate report.
2. Trial count was logged honestly and Deflated Sharpe z > 0 at that count.
3. `AlphaModule.is_ready()` returns True only for the ROBUST alpha; all others return False.
4. Risk audit (docs/audits/RISK_AUDIT_*.md) dated AFTER the last code change, all PASS.
5. Test suite green: `python3 -m pytest tests/ -q`.
6. Secrets: none in repo; broker keys exist ONLY on the VPS WORKER; cloud side has none.
7. Safety hooks active in `.claude/settings.json` (bash_guard, file_guard, session-start).
8. For LIVE specifically: 30-day dry-run journal exists with no risk-guard violations,
   and the owner — a human — flips `LIVE_TRADING` themselves. The agent never does.

Output: checklist with evidence per item, then a single verdict line: GO or NO-GO (+ blockers).
$ARGUMENTS
