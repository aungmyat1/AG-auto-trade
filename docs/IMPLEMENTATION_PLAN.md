# Implementation Plan — v4 (2026-06-12)

Maps the generic "trading bot architecture" (data → signal → risk → execution → monitoring)
onto this repo, optimized for what already exists and what is locked. Companion to
`docs/PROJECT_STATE.md` (live memory) and `GROUND_TRUTH.md` (locked decisions).

## 1. Reconciliation with the generic architecture

What the standard blueprint gets right is already this repo's design. What it gets wrong
for us is anything that re-opens closed lines.

| Blueprint concept | AG reality | Action |
|---|---|---|
| Layered pipeline: data → signal → risk → execution → monitoring | `AlphaModule.propose()` → `RiskEngine.validate_entry()` → (Phase 3 execution) → journal → Telegram | Already the architecture — keep |
| Strategy base class, signals never place trades | `ag/alpha/base.py::AlphaModule` returns `SignalProposal`; risk engine decides | Already built — keep |
| Dynamic strategy plugin loader | Exactly three race entrants (A1/A2/A3) through one gate | Reject — a fixed registry of 3; plugin sprawl killed the old repo |
| Market data: Bybit/Binance/MEXC, orderbook/funding/liquidations | Venue locked: CME GC/MGC + 6E. History = Databento, live = IB (Phase 3). Crypto line CLOSED (`research_archive/`) | Replace with `ag/data/databento/` loader; no perp-specific feeds |
| SMC as entry signal (sweep + BOS = buy) | Hard rule 3: SMC answers WHERE only; momentum/delta answers WHEN. SMC entry authority is archived FRAGILE | Reject — A1 implements the filter/trigger split |
| Risk numbers: 1%/trade, 3% daily, 5 positions | Locked stricter: 0.5%/trade, 2% daily, 6% weekly, 15% max DD, 3 concurrent | Reject blueprint numbers — ours are locked |
| Validation ladder: backtest → WF → OOS → paper → small live | Locked gate is stricter: floor (n≥50, gross PF>1) → ROBUST (n≥200, net PF>1.25, CPCV/WF/MC/DSR) → 30-day dry-run → OWNER flips live | Keep the principle; the gate supersedes it |
| `ai/strategy_optimizer.py` | Rule: validation before optimization; every trial inflates DSR `--n-trials` | Reject pre-gate; build a trial registry instead |
| Dashboard | Telegram alerts exist (stdlib) | Defer until something runs live |
| "Only one trade across hundreds of pair-days" warning | Real lesson from the archived crypto line (v1 zero-signal bug; H1 probe 1 trade/365d) | Adopt as an explicit A1 acceptance criterion: minimum signal rate before any quality claim |

## 2. Current state (delta to plan)

Validation core done (21 tests green). Skeleton packages exist for alpha/data/execution/
infrastructure. Risk engine + regime classifier implemented but untested. **New finding
(2026-06-12): G5 leverage guard in `RiskEngine.validate_entry()` is a no-op** — documented
as one of six non-bypassable guards but enforces nothing (`ag/risk/engine.py:121`).

## 3. Phases

### Phase A — Platform hardening (now; blocks everything else)

| # | Work item | Where |
|---|---|---|
| A1 | Risk engine tests: trip + pass cases for G1/G2/G3/G4/G6, multi-violation reporting, `record_trade_result` state (peak tracking, cooldown reset on win), `reset_daily`, risk-score bounds | `tests/unit/test_risk_engine.py` |
| A2 | Implement G5: `validate_entry(..., leverage: float = 1.0)` rejects `leverage > config.max_leverage`; test it. Strengthens a guard — does not touch any gate threshold | `ag/risk/engine.py` |
| A3 | Regime classifier tests: synthetic OHLCV fixtures per regime (trend/chop/squeeze/expansion), `size_multiplier` mapping, **no-look-ahead check** (classification at bar *i* must not change when later bars are appended) | `tests/unit/test_regime_classifier.py` |
| A4 | Lock-before-look consistency test: parse thresholds out of `GATE_DECISION.md` and assert equality with `ag/config.py` `GATE_*` constants — any drift is a red test. Closes the "no code reads GATE_DECISION.md" gap | `tests/unit/test_lock_before_look.py` |

Exit: full suite green, ruff clean, PROJECT_STATE updated.

### Phase B — Data layer (Databento, futures-specific)

| # | Work item | Where |
|---|---|---|
| B1 | Historical OHLCV loader for GC/MGC/6E (1m + 1h), local parquet cache, `DATABENTO_API_KEY` from env only | `ag/data/databento/loader.py` |
| B2 | Continuous-contract policy: volume-crossover roll; back-adjusted series for signals, raw per-contract prices for fills/costs. Document the rule in the module | same |
| B3 | Integrity checks: CME session calendar (aligned to `config.SESSIONS`), gap/duplicate/monotonicity validation | `ag/data/databento/integrity.py` |
| B4 | Small offline fixture bundle so CI never needs the network | `tests/fixtures/` |

Exit: loader + integrity tests green offline; one cached GC dataset reproducible by command.

### Phase C — Alpha modules (the race entrants)

All three implement `AlphaModule.propose(market_data) -> SignalProposal | None`. None ever
places a trade; `is_ready()` stays False until a ROBUST verdict exists.

| # | Work item | Notes |
|---|---|---|
| C1 | **A1** `a1_smc_momentum/`: `zones.py` (order blocks, FVG, sweeps, premium/discount = WHERE), `trigger.py` (momentum/delta = WHEN), `module.py`. H1+ timeframe only (5m archived FAIL), structure-based stops, session windows + news buffer from config | Acceptance gate: ≥ 50 trades on the GC validation window *before* any quality discussion (floor-n; the old system's zero-signal failure mode) |
| C2 | **A2** `a2_master_trader/`: ingest SignalStart dataset (4,437 trades), survivorship-honest (include the trader's full record), entry at next available price + conservative slippage; gate it net-of-cost as its own trade series | Open decision for owner: validate on instruments the master actually traded vs. mapping onto GC/6E |
| C3 | **A3** `a3_ensemble/`: `0.4·A1 + 0.3·regime + 0.3·A2 > 0.75`; requires A1/A2 confidence outputs + `RegimeResult`. Build last | Weights are pre-registered in GATE_DECISION.md — not tunable |
| C4 | Trial registry: append-only JSONL logging every parameter set/threshold evaluated per alpha; the only honest source for `--n-trials` | `ag/validation/trial_log.py` |
| C5 | Backtest harness: replay history through alpha **and** `RiskEngine.validate_entry()` (risk path exercised even offline), emit trades CSV for the gate | `scripts/run_alpha_backtest.py` |

Exit: each alpha unit-tested (detector correctness, no repainting — `/smc-review` for A1),
each produces a net-of-cost trades CSV on GC history, every trial logged.

### Phase D — Gate race

Run `scripts/run_gate.py <alpha>.csv --instrument GC --cost-preset gc --n-trials <from registry>`
for A1/A2/A3 — identical gate, GC primary, 6E separately (per-instrument models). Record
verdicts in `VALIDATION_STATUS.md` + `PROJECT_STATE.md`; FRAGILE → `research_archive/` with
verdict header; send `alert_validation_result()`. **"No alpha passes" is a valid outcome —
stop there; never relax thresholds.**

### Phase E — Execution (only if a ROBUST verdict exists)

Nautilus + IB on the VPS WORKER (the only key holder). The blueprint's execution concerns —
partial fills, reconnects, rate limits, zero strategy logic in the executor — land here and
not earlier. Then 30-day dry-run with journal-vs-backtest expectancy drift tracking; only the
OWNER flips `LIVE_TRADING`.

## 4. Explicitly not building

Bybit/Binance/MEXC feeds, orderbook/funding/liquidation data, BTCUSD/EURUSD paper trading
(crypto line is closed), a strategy plugin loader, additional strategies (trend-following /
mean-reversion / breakout queue *behind* the race and a `research_archive/` read), any AI
strategy optimizer before a floor-gate pass, dashboards.

## 5. Order and sizing

A (S — tests + one guard fix) → B (M — loader + roll policy) → C1/C2 in parallel (L each) →
C3 (S) → D (S compute-heavy) → E (L, gated on ROBUST). Phases A–B have no open decisions;
the single owner decision before C2 is the A2 instrument-mapping question above.
