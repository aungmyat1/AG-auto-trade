# AG Auto Trade — Agent Rules

Validation-first futures trading system. **The gate is the asset; every strategy is just a candidate.**

**Always read `docs/PROJECT_STATE.md` first** — it is the live project memory (current stage,
verdicts, next goal). Update it whenever stage, verdicts, or goals change.

## Hard Rules (locked — see GROUND_TRUTH.md)

1. **Never enable live trading.** `LIVE_TRADING` stays off until: ROBUST gate verdict
   (n ≥ 200 net trades) → 30-day dry-run → the OWNER flips it manually. Not the agent. Ever.
2. **Never modify `ag/validation/lock_before_look/GATE_DECISION.md`** — thresholds were
   pre-registered before any alpha saw data. Never relax thresholds anywhere
   (`ag/validation/gate.py`, `ag/config.py`). "No alpha passes" is a valid result.
3. **SMC is a context filter only** — it answers WHERE, never WHEN. It must never generate
   entries. Crypto SMC is already FRAGILE (see `research_archive/legacy_smc_failures/`).
4. **No alpha gets primacy by assertion.** A1 (SMC-filter + momentum), A2 (master-trader copy),
   A3 (ensemble) race through the IDENTICAL gate. FRAGILE → `research_archive/` with a verdict
   header; never deleted, never quietly re-tested.
5. **Risk engine is non-bypassable.** Every entry path calls `RiskEngine.validate_entry()`
   (6 guards: daily loss, drawdown, cooldown, size, leverage, concurrency). 0.5%/trade,
   2% daily, 6% weekly, 15% max DD.
6. **Net-of-cost only.** A profit factor without CME commission + spread + slippage applied
   is not a result. Use `CostModel.for_gc()` / `.for_6e()`.
7. **Count every trial.** Every threshold, variant, and parameter combo tried inflates the
   Deflated-Sharpe trial count (`--n-trials`). Under-reporting trials is self-deception.
8. **Never commit secrets.** Keys live in env vars / `.env` (gitignored). Cloud agents hold
   NO broker keys; only the VPS WORKER owns IB keys and may trade.
9. **Every code change needs tests.** Run `python3 -m pytest tests/ -q` before claiming done.
   Validation before optimization — never tune a strategy that hasn't passed the floor gate.
10. **No duplicate subsystems.** The old repo died with 7 duplicated pairs (two risk engines,
    two strategy trees, two exchange clients…). One implementation per concern, always.

## Current Stage

Phase 0–6 of the v4 plan complete (validation core + risk + regime). **Next: alpha modules
A1/A2/A3 to the common `AlphaModule` interface, then the gate race.** Execution (Nautilus + IB)
is Phase 3 and must not be built until a ROBUST verdict exists.

## Architecture

```
Alpha (propose) → RiskEngine.validate_entry() → [Phase 3: execution] → journal → Telegram
                          ↑ everything above runs only what the gate has passed
ag/validation/   gate battery: CPCV · purged WF · Monte Carlo · Deflated Sharpe · cost model
ag/risk/         6-guard engine (non-bypassable)
ag/regime/       ADX/ATR/HTF classifier — 4 regimes
ag/alpha/        AlphaModule interface + A1/A2/A3
ag/monitoring/   Telegram alerts (stdlib only)
research_archive/  validated NEGATIVE results — read before proposing any "new" idea
```

## Instruments / Venue

GC/MGC + 6E (CME futures). History: Databento. Live (Phase 3 only): Interactive Brokers.
Primary validation instrument: **GC**. Per-instrument models — never share one model across
GC and 6E.

## Commands

```bash
python3 -m pytest tests/ -q                                  # full suite — must be green
python3 scripts/run_gate.py trades.csv --instrument GC \
    --cost-preset gc --n-trials <honest count>               # gate battery on a trades CSV
python3 -m ruff check ag/ tests/                             # lint
```

Slash commands: `/validate-strategy` `/backtest` `/check-risk` `/audit-repo` `/gate-status`
`/deployment-check`. Skills in `.claude/skills/` load automatically when relevant.

## Safety hooks (active via .claude/settings.json)

- Secret scan before any `git commit`; tests must pass before any `git push`.
- Edits to GATE_DECISION.md, gate thresholds, or `LIVE_TRADING=True` are blocked.
- Do not disable or work around these hooks; if one blocks a legitimate change, stop and
  tell the owner what was blocked and why.
