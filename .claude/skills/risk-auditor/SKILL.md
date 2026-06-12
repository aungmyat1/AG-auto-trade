---
name: risk-auditor
description: Audit risk-management integrity. Use when execution or alpha code changes, when asked to check risk, before any deployment decision, or when position sizing / limits / guards are discussed.
---

# Risk Auditor

The risk engine is non-bypassable by design. This audit proves (or disproves) that the
codebase still honors that.

## Checklist

1. **Single engine.** Exactly one risk engine exists: `ag/risk/engine.py::RiskEngine`.
   Grep for any second implementation (`class.*Risk`, `validate_entry`) — duplicates are
   forbidden (the old repo had two risk engines AND two circuit breakers).

2. **Every entry path is guarded.** For each call site that could open a position
   (today: none should exist outside tests; Phase 3: `ag/execution/`), verify
   `RiskEngine.validate_entry()` is called BEFORE the order, and `approved=False`
   aborts the trade with no retry-around.

3. **No bypass surface.** Grep for: `approved\s*=\s*True` hardcoded, `bypass`, `skip_risk`,
   `force=True` near order paths, try/except swallowing a RiskDecision, or code mutating
   `RiskConfig` at runtime.

4. **Constants match the plan.** `RiskConfig` and `ag/config.py` must agree:
   0.5%/trade, 2% daily, 6% weekly (advisory), 15% max DD, 3 concurrent, cooldown after
   3 consecutive losses. Flag drift in either direction.

5. **Gate coupling.** `AlphaModule.is_ready()` must return False without a ROBUST verdict;
   nothing may route a proposal from a module where `is_ready()` is False.

6. **Live-trading flag.** Confirm no `LIVE_TRADING` truthy assignment exists anywhere
   (the file_guard hook blocks the agent writing one, but audit for human-introduced ones).

7. **State hygiene.** `record_trade_result()` is called on every close; `reset_daily()`
   has an owner at the day boundary; G5 leverage is enforced at the execution layer once
   that layer exists (it is advisory in the engine — flag this until Phase 3 closes it).

## Output

Write `docs/audits/RISK_AUDIT_<YYYY-MM-DD>.md`: PASS/FAIL per item, file:line evidence
for every finding, and a single overall verdict. A FAIL on items 1–3 or 6 means
**no deployment conversation may proceed** until fixed.
