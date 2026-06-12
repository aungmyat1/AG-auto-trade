# Git Setup & Workflow

Reference for contributors and the agent working on this repo.

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready; always passes tests + lint |
| `feature/*` | New detectors, alpha modules, infrastructure |
| `hotfix/*` | Critical bug fixes (fast-tracked to main) |
| `research/*` | Experimental SMC concepts (may not pass gate; never merged until gated) |
| `dispatch-N-*` | Agent dispatch branches (one per Dispatch session) |

**Rule:** Never commit directly to `main` for multi-file changes. Open a PR so
the PR template checklist runs.

---

## Commit Convention

```
feat(scope): short description        # new capability
fix(scope): short description         # bug fix
docs: short description               # documentation only
test(scope): short description        # tests only
refactor(scope): short description    # no feature/fix change
chore: short description              # maintenance, deps, CI
lock: short description               # lock-before-look spec committed
```

Examples:
```
feat(smc): add FVG detector with ATR filtering
fix(risk): correct drawdown calculation for consecutive losses
docs: update Phase 1 runbook with reconciliation notes
test(gate): add cost shock stress tests
lock: A1 SMC-momentum decision pre-registered before gate run
```

Scope examples: `smc`, `risk`, `regime`, `gate`, `a1`, `a2`, `monitoring`, `ci`

---

## Pre-commit Hooks (active)

Configured in `.claude/settings.json`. The hooks run automatically on
`git commit` and block if they detect:

1. **Secret patterns** — any line matching key/token/password patterns.
   Do NOT add credentials to any tracked file. Keep keys in `.env` (gitignored).

2. **Live-trading flag** — the live-trading flag may only be set by the owner
   after a ROBUST verdict + 30-day dry-run. The agent must never enable it.

3. **`GATE_DECISION.md` edits** — locked thresholds may not be modified.

4. **Test failures** — `python3 -m pytest tests/ -q` must pass before push.

If a hook blocks a legitimate change, stop and report what was blocked and why.
Do NOT use `--no-verify` to bypass hooks.

---

## Lock-before-Look Protocol

Any new alpha spec must have its `GATE_DECISION` document committed to
`ag/validation/lock_before_look/` **before** the alpha sees any data.

Steps:
1. Write spec file: `ag/validation/lock_before_look/<ALPHA_ID>_DECISION.md`
2. Commit with message: `lock: <alpha-id> spec pre-registered before gate run`
3. Only then: build the alpha, run the gate

Retroactive specs are not valid. "No alpha passes" is a valid result.

---

## Day-to-Day Workflow (agent dispatches)

```bash
# Start a dispatch
git checkout -b dispatch-N-description

# Work…
python3 -m pytest tests/ -q     # must stay green throughout
python3 -m ruff check ag/ tests/

# Commit when a logical unit is done
git add <specific files — never git add -A>
git commit -m "feat(scope): description"

# Push only when dispatch is complete and tests pass
git push origin dispatch-N-description
```

---

## Merge Policy

- PRs require: tests green + lint clean + PR template checklist complete.
- Safety gates (GATE_DECISION.md untouched, live-trading flag owner-controlled,
  no bypass) are mandatory checklist items — do not merge if any are unchecked.
- Squash-merge preferred for feature branches to keep `main` history linear.
- research/* branches: merge only after a ROBUST gate verdict exists for the
  alpha under development. Read/Fragile results stay in `research_archive/`.

---

## research_archive/ Policy

When an alpha or strategy receives a FRAGILE verdict (or is deprecated):

1. Move all strategy-specific code to `research_archive/<name>/`
2. Add `VERDICT.md` at the top of that directory:
   ```
   # VERDICT: FRAGILE
   Tested: YYYY-MM-DD
   Gate criteria failed: [list]
   Key metrics: PF=X, SR=Y, DD=Z%
   Why it failed: [brief analysis]
   DO NOT re-test without a new lock-before-look spec.
   ```
3. Commit as: `chore: archive <name> — FRAGILE verdict YYYY-MM-DD`

`research_archive/` is **never** deleted. It is the project's validated-negative
knowledge base. Check it before proposing any "new" idea.
