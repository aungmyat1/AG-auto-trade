---
name: Feature request
about: Suggest a new SMC concept, strategy module, or infrastructure improvement
title: 'feat: '
labels: enhancement
assignees: ''
---

## Is your feature request related to a problem?

A clear description of the problem. Example: "A1 generates too few signals because..."

## Proposed solution

Describe the solution. For new SMC concepts, include:
- Concept name and definition
- Detection logic (pseudocode or reference)
- Expected signal frequency (estimate)
- How it relates to existing WHERE/WHEN filters

## Gate compliance

- [ ] New alpha spec will have a lock-before-look document committed **before** any backtest
- [ ] Proposed thresholds do not modify `GATE_DECISION.md` (locked)
- [ ] Live-trading flag remains owner-controlled (ROBUST verdict + dry-run required first)

## Alternatives considered

Any other solutions or features considered and why they were ruled out.

## Additional context

Any other relevant information, diagrams, or references.
For SMC concepts: cite the source and whether it has been validated in any prior research
(check `research_archive/` for negative results first).
