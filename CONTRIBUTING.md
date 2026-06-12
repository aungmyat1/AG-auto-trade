# Contributing to AG-auto-trade

Thank you for your interest in contributing.

## Code of Conduct

- All changes that affect trading logic must pass the Validation Gate before use.
- Never bypass safety hooks or validation requirements.
- Risk management, auditability, and test coverage are non-negotiable.
- This is a high-stakes financial project. Quality and safety come first.

## Project Rules (from CLAUDE.md — hard constraints)

1. **Never enable live trading.** The live-trading flag stays off until:
   ROBUST gate verdict (n ≥ 200 net trades) → 30-day dry-run → owner flips it manually.
2. **Never modify `ag/validation/lock_before_look/GATE_DECISION.md`** — thresholds were
   pre-registered before any alpha saw data. Never relax them in `gate.py` or `config.py`.
3. **No alpha gets primacy by assertion.** A1/A2/A3 race through the identical gate.
   New alpha specs require a lock-before-look document committed before any gate run.
4. **No duplicate subsystems.** One implementation per concern. Check existing code
   before adding risk, monitoring, or cost logic.

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes following the commit convention below
4. Run `python3 -m pytest tests/ -q` — all tests must pass
5. Run `python3 -m ruff check ag/ tests/` — lint must be clean
6. Submit a Pull Request using the PR template

## Pull Request Requirements

- **Tests required**: every code change needs a test (`tests/unit/` or `tests/validation/`)
- **SMC concepts**: must be in `ag/alpha/a1_smc_momentum/detectors/` (not `research_archive/`)
  and pass the `SMC_CONCEPT_VALIDATION_CHECKLIST.md`
- **Risk changes**: include unit tests; do not relax guard thresholds
- **`docs/PROJECT_STATE.md`**: update if stage, verdicts, or goals change
- **PR title**: conventional commit format (see below)

## Commit Convention

```
feat(scope): short description        # new capability
fix(scope): short description         # bug fix
docs: short description               # documentation only
test(scope): short description        # tests only
refactor(scope): short description    # no feature/fix change
chore: short description              # maintenance
```

Examples:
```
feat(smc): add FVG detector with ATR filtering
fix(risk): correct drawdown calculation for consecutive losses
docs: update Phase 1 runbook with reconciliation notes
test(gate): add cost shock stress tests
```

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready; always passes tests |
| `feature/*` | New features and alpha development |
| `hotfix/*` | Critical bug fixes |
| `research/*` | Experimental SMC concepts (may not pass gate) |
| `dispatch-N-*` | Agent dispatch branches |

## Research Archive

Strategies that fail the gate go to `research_archive/` with a `VERDICT.md` file.
They are **never deleted** and **never quietly re-tested** without a new lock spec.
Check this folder before proposing any "new" idea — it may already be validated-negative.

## Questions?

Open an issue with the label `question`.
