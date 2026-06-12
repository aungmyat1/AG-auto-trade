# AG-auto-trade — Project Overview

**Repository**: https://github.com/aungmyat1/AG-auto-trade
**Primary Objective**: Develop and operate a profitable automated trading system based on Smart Money Concepts (SMC) using rigorous validation before any live capital exposure.
**Architecture Philosophy**: Validation-first, agent-augmented trading engineering operating system.

---

## High-Level Architecture

```
ag/
├── validation/          # Gate decision engine (non-negotiable)
├── risk/                # Position sizing, drawdown control, Kelly
├── regime/              # Market regime detection
├── alpha/               # Strategy implementations (a1, a2, a3…)
├── execution/           # Broker connectors (future)
├── monitoring/          # Alerts, logging, dashboards
└── infrastructure/      # VPS, deployment, secrets

research_archive/        # Legacy failures + concept research
docs/                    # All project documentation
.claude/                 # Agent operating layer (skills, commands, memory)
```

---

## Core Principles

1. **No Live Trading Without Gate Pass** — Every strategy must pass the validation gate.
2. **Realistic Cost Modeling** — Slippage, spread, commission modeled from day one.
3. **SMC Core** — Order Blocks, Fair Value Gaps, Liquidity, BOS/CHOCH, Inducement, Displacement.
4. **Agent-Augmented Development** — Claude skills handle validation, risk audit, SMC review, etc.
5. **Full Auditability** — Every decision, backtest, and live trade logged.

---

## Current Technology Stack (2026-06-12)
- Python 3.x + pytest
- GitHub Actions CI
- Telegram alerting (stdlib)
- Structured validation + risk modules
- Research archive for SMC failures

---

## Key Constraints
- Must survive legacy SMC strategy failures (documented in research_archive)
- Realistic market microstructure modeling required
- Strict separation between research and live execution

---

## Documentation Index
- `ROADMAP.md` — Full phased plan
- `VALIDATION_STATUS.md` — Current alpha verdicts (all PENDING)
- `CLAUDE.md` — Agent operating rules (in repo)
- `PROJECT_STATE.md` — Live project memory (in repo)
- `GROUND_TRUTH_OLD_SYSTEM.md` — Reference of previous failures

This project is designed for long-term sustainable profitability, not quick wins.
