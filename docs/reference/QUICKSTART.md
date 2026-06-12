# AG-auto-trade Quickstart Guide

## 1. Clone & Setup
```bash
git clone https://github.com/aungmyat1/AG-auto-trade.git
cd AG-auto-trade
pip install -e .
```

## 2. Run Tests
```bash
pytest
# Expected: 21/21 passed
```

## 3. Key Files to Review First
- `README.md` — Project overview
- `docs/PROJECT_STATE.md` — Current live memory
- `docs/VALIDATION_STATUS.md` — Alpha status
- `.claude/CLAUDE.md` — Agent rules & safety hooks

## 4. Next Steps (Recommended Order)
1. Read `ROADMAP.md` (in this docs folder)
2. Review `VALIDATION_GATE_SPEC.md`
3. Start Phase 1 work on validation gate hardening
4. Use `/smc-review` slash command for any new SMC concept

## 5. Safety Notes
- Never bypass `GATE_DECISION` or `LIVE_TRADING` flags
- All secrets are scanned before commit
- Pre-push hooks enforce test passing

This project follows a strict validation-first philosophy. No shortcuts.
