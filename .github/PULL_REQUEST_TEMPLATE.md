## Description

<!-- Brief summary of changes. What problem does this solve? -->

## Type of change

- [ ] Bug fix
- [ ] New SMC concept / detector
- [ ] New alpha module or strategy logic
- [ ] Documentation update
- [ ] Refactoring / performance
- [ ] Risk / validation infrastructure change

## Checklist

### Always required
- [ ] All tests pass: `python3 -m pytest tests/ -q`
- [ ] Lint clean: `python3 -m ruff check ag/ tests/`
- [ ] No secrets or large data files added
- [ ] `docs/PROJECT_STATE.md` updated if stage, verdict, or goals changed

### Safety gates (tick ALL that apply)
- [ ] `GATE_DECISION.md` not modified (thresholds are locked — any change requires new lock-before-look doc)
- [ ] `LIVE_TRADING` is not set to `True` anywhere
- [ ] No alpha saw data before its lock-before-look spec was committed
- [ ] Risk engine guards not bypassed or thresholds relaxed

### For new SMC concepts
- [ ] Detector is in `ag/alpha/a1_smc_momentum/detectors/` (not `research_archive/`)
- [ ] Unit tests cover: detects correctly, does NOT detect on flat data, mitigation logic
- [ ] Signal funnel counter wired up (`audit_tracker.record(...)`)

### For new alpha modules
- [ ] Lock-before-look spec committed **before this PR** (in `ag/validation/lock_before_look/`)
- [ ] `is_ready()` returns `False` (no ROBUST verdict yet)
- [ ] `propose()` calls `RiskEngine.validate_entry()` in the execution path

## Related issues

<!-- Link any related issues: Closes #N -->

## Testing

<!-- How was this tested? Include the pytest output summary. -->

## Signal funnel report (if SMC-related)

```
Paste tracker.report() output here, or write N/A.
```
