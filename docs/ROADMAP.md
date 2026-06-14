# AG Auto-Trade — Live Roadmap
> Last synced: 2026-06-14 · Source of truth: `docs/PROJECT_STATE.md`
>
> Two views of the same journey:
> • **Build phases (A–E)** — what gets built, in locked order.
> • **Verification ladder (PHASE 0–11)** — how each layer is *proven* before it earns live capital.
> The ladder is adopted from the owner's verification framework (2026-06-14) and reconciled
> with the locked decisions in `GROUND_TRUTH.md` / `GATE_DECISION.md`. Where the framework and
> the locked rules disagree, **the locked rules win** — see "Reconciliation" below.

---

## System Pipeline (end-to-end)

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                          SIGNAL PIPELINE                                  │
 │                                                                           │
 │  ┌──────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
 │  │     DATA     │───▶│  ALPHA   │───▶│   RISK   │───▶│ EXECUTE  │       │
 │  │  IB (MVP)    │    │ propose()│    │ validate │    │  IB/Naut │       │
 │  │  Databento ↑ │    │  (WHERE  │    │ 6 guards │    │          │       │
 │  └──────────────┘    │  +WHEN)  │    └──────────┘    └──────────┘       │
 │                      └──────────┘                                        │
 │     🟡 B  ←  first download pending    ✅ done          🔒 D/E           │
 │                                                                           │
 │  ◀────────── GATE required before execution layer may be built ─────────▶│
 └──────────────────────────────────────────────────────────────────────────┘
```

SMC sits inside ALPHA as the **WHERE** filter only — it never emits an entry by itself
(`GROUND_TRUTH.md` §3). A momentum/delta trigger decides **WHEN**. The risk engine, not the
strategy, decides size and whether the trade is allowed.

---

## Phase Progress (build view)

```
Phase A  Platform hardening     ████████████████████  100%  ✅ DONE
Phase B  Data layer             ████████████████░░░░   80%  🟡 FIRST DOWNLOAD PENDING
Phase C  Alpha gate race        ████░░░░░░░░░░░░░░░░   20%  🟡 WAITING ON DATA
Phase D  Execution (IB/Naut)    ░░░░░░░░░░░░░░░░░░░░    0%  🔒 LOCKED (needs ROBUST)
Phase E  Live trading           ░░░░░░░░░░░░░░░░░░░░    0%  🔒 LOCKED (owner-only flip)
```

Deployment state: **`NOT_READY`** → `READY_FOR_PAPER` → `READY_FOR_SHADOW` →
`READY_FOR_LIVE_PILOT` → `READY_FOR_SCALE`. No state may be skipped.

---

## ══════════════ YOU ARE HERE ══════════════

```
┌─────────────────────────────────────────────────────────┐
│  🟡  CURRENT TASK — two parallel tracks                 │
│                                                         │
│  TRACK 1: IB plumbing test (free, immediate)            │
│  Goal: verify the pipeline runs end-to-end.             │
│  Result label: PLUMBING CHECK — not an edge verdict.    │
│                                                         │
│  pip install -e ".[dev]" && pip install ib_insync       │
│  cp .env.ib.example .env   # set IB_PORT=7497           │
│  python3 -c "                                           │
│    from ag.data.loader import get_loader                │
│    df = get_loader('ib').load(                          │
│        'GC','1h',start='2024-01-01',end='2024-12-31')   │
│    print(df.shape)"                                     │
│  # → IB max: READ-tier glance only (1 regime, 1 year)  │
│  # → NOT valid input for the ROBUST gate                │
│                                                         │
│  TRACK 2: Databento subscription (gate-grade data)      │
│  Goal: multi-year multi-regime GC 1m bars for ROBUST.   │
│  A0_MVP_DECISION.md specifies Databento — not IB.       │
│                                                         │
│  Add DATABENTO_API_KEY to .env, then:                   │
│  python3 -c "                                           │
│    from ag.data.loader import get_loader                │
│    df = get_loader('databento').load(                   │
│        'GC','1m',start='2022-01-01',end='2024-12-31')"  │
│                                                         │
│  THEN (after Databento data lands):                     │
│    scripts/run_alpha_backtest.py --alpha a0_mvp         │
│    → log every parameter tune in trial_log.py first    │
│    scripts/run_gate.py trades.csv --instrument GC \     │
│      --n-trials <honest count from trial_log>           │
└─────────────────────────────────────────────────────────┘
```

---

## Verification Ladder (PHASE 0–11) — path to live

Adopted from the owner's 2026-06-14 framework. Each rung must PASS before the next is attempted;
a failure routes back through the **Master Correction Loop** (bottom). The ladder maps onto the
build phases and the locked gate — it does **not** replace them.

| # | Verification phase | Maps to | Status | Exit criterion (reconciled) |
|---|--------------------|---------|--------|------------------------------|
| 0 | Architecture audit | Phase A · `/audit-repo` | ✅ | Implementation matches `GROUND_TRUTH.md`; risk engine non-bypassable; no alpha calls a broker; journal/kill-switch exist (kill-switch = Phase D, locked) |
| 1 | Code quality | CI | 🟡 | `ruff` clean (10 nits open) · **add `mypy`, `bandit`, `pip-audit` to CI** (not yet wired) · 0 high security findings |
| 2 | Component testing | Phase A | ✅ | SMC detectors + risk + regime unit-tested; coverage target ≥ 90% on core (measure with `pytest-cov`) |
| 3 | Integration testing | Phase A | ✅ | `tests/integration/` — detector→pipeline→signal and risk-in-loop both covered |
| 4 | Historical replay / no-lookahead | Phase C · `/smc-review` | 🟡 | Bar-by-bar replay only (`history = candles[:i]`); **no future leak, no repainting** — re-audit each alpha before its gate run |
| 5 | Backtesting validation | Phase C/D · **the locked gate** | ⬜ | **Locked gate** (see below) on **GC/MGC/6E** net-of-cost. Not the framework's PF>1.3/500-trades and not crypto — see Reconciliation |
| 6 | Risk engine verification | Phase A | ✅ | 6 guards proven (35 tests); sizing = 0.5%/trade, daily 2%, DD 15% — **locked numbers**, not the framework's 3%/10% |
| 7 | Infrastructure resilience | Phase D | 🔒 | API-down / DB-fail / VPS-reboot / net-outage / webhook-fail → safe-mode + state recovery. Built only after a ROBUST verdict |
| 8 | Paper trading (30–60d) | Phase E dry-run | 🔒 | = the locked **30-day dry-run**. No crashes, risk rules obeyed, expectancy tracked vs backtest |
| 9 | Shadow trading (30d) | Phase E | 🔒 | Production logic, virtual orders; live result vs expected stays stable. **New rung — adopted** |
| 10 | Live capital pilot | Phase E | 🔒 | Owner-only flip after ROBUST + dry-run. Ramp $100→$250→$500→$1000; scale only on sustained edge (not "30 trades positive" alone) |
| 11 | Scale-up verification | Phase E | 🔒 | Slippage/latency/spread/capacity stable at 10k→50k→100k sims |

Deployment-state gates: **`READY_FOR_PAPER`** requires 0–6 green; **`READY_FOR_SHADOW`** adds 8;
**`READY_FOR_LIVE_PILOT`** adds 9 **and a ROBUST gate verdict**; **`READY_FOR_SCALE`** adds 11.

---

## Reconciliation with locked decisions (where the framework is overridden)

The owner's framework is a strong verification spine, but five points conflict with pre-registered
locked rules. The locked rules win — these are not negotiable post-data:

1. **Backtest instruments = CME GC/MGC + 6E only.** The framework lists XAUUSD / BTCUSDT / ETHUSDT.
   Crypto is the **closed** line (archived FRAGILE/FAIL in `research_archive/`), and spot XAUUSD ≠ GC
   futures. Per-instrument models, GC primary. No crypto re-entry.
2. **Phase-5 pass bar = the locked gate, not PF>1.3 / 500 trades.** The immutable gate is *stricter and
   multi-dimensional*: n ≥ 200 net trades, **net** PF > 1.25, Sharpe > 1.2, DD < 15%, WR > 45%, CPCV
   median PF > 1.0, WF ≥ 60%, MC p5 PF > 0.9, DSR z > 0. Thresholds were registered before data and
   **cannot be changed** — not even to the framework's numbers (`GATE_DECISION.md`).
3. **Risk limits stay locked:** 0.5%/trade, **2%** daily (not 3%), 6% weekly, **15%** max DD (not 10%),
   ≤5× leverage, ≤3 concurrent. The framework's $50-on-$10k sizing already matches; its loss limits do not.
4. **SMC never generates entries** (§3). The framework's "…→ FVG → OB → **Signal**" pipeline is allowed
   only as the **WHERE** context; a momentum/delta trigger supplies **WHEN**. A ChoCH→entry alpha is the
   archived `SMC_H1_FRAGILE` pattern — A0_MVP runs it solely as a *plumbing check*, expected FRAGILE.
5. **Live promotion is owner-only and gate-gated.** Framework Phase 10's "scale after 30 trades +
   positive expectancy" is an in-pilot *monitor*, **not** the promotion criterion. Live requires:
   ROBUST gate verdict → 30-day dry-run pass → owner manually flips the flag. Never the agent. Ever.

**Already core (not "future work"):** the framework suggests adding walk-forward / Monte-Carlo / CPCV
*after* Phase 5 — these are already inside the locked gate today. **Adopted as enhancements:** `mypy` +
`bandit` + `pip-audit` in CI (Phase 1); a **30-day shadow-trading** rung (Phase 9); and "**beat a simple
trend-following baseline**" as an additional hurdle in the race — each variant counts as +1 DSR trial.

---

## Phase A — Platform & Validation Core ✅

| Item | Status | Evidence |
|------|--------|----------|
| Validation gate (CPCV · WF · MC · DSR · cost model) | ✅ | 45 tests |
| Gate thresholds locked pre-data | ✅ | `GATE_DECISION.md` (immutable) |
| Lock-before-look consistency test (CI) | ✅ | `test_lock_before_look.py` |
| Risk engine — 6 guards, non-bypassable | ✅ | 35 tests, G5 fixed Dispatch 4 |
| Regime classifier | ✅ | 16 tests |
| SMC detectors (OB · FVG · BOS/ChoCH · sweep) | ✅ | 58 tests |
| A1SmcMomentum wrapper + audit tracker | ✅ | pipeline + backtest tests |
| Trial registry (honest --n-trials) | ✅ | `ag/validation/trial_log.py` |
| Backtest harness | ✅ | `scripts/run_alpha_backtest.py` |
| Test suite: unit · integration · backtest · e2e | ✅ | **498 passed · 17 skip** (deps absent) |
| CI (GitHub Actions) + branch protection | ✅ | PR required + test check |

---

## Phase B — Data Layer 🟡 FIRST DOWNLOAD PENDING

> **Loaders built. Cache-hit path tested. One TWS session away from real data.**

| Step | Status | Notes |
|------|--------|-------|
| B0 — IB loader (`IBHistoricalLoader`) | ✅ | Offline-first, CONTFUT, chunked pacing |
| B0 — Databento loader (`DatabentoLoader`) | ✅ | Offline-first, lazy import, parquet cache |
| B0 — Source-agnostic factory (`get_loader`) | ✅ | Identical `.load()` API on both — one flag to switch |
| B0 — CME roll calendar (`roll.py`) | ✅ | `get_front_month()` for GC/MGC/6E |
| B0 — Integrity checker (`check_ohlcv`) | ✅ | C1–C8, shared across both loaders |
| B0 — Synthetic fixtures + data tests | ✅ | pass · 17 skip (pyarrow/ib_insync absent) |
| **B1 — IB plumbing download** | 🟡 **NEXT** | Start TWS → `loader.load("GC","1h",…)` — READ-tier only |
| B2 — Integrity check on downloaded data | ⬜ | `check_ohlcv(df,"GC","1h")` — auto after download |
| **B3 — Databento 1m bars (gate-grade)** | 🔴 **BLOCKED** | Needs `DATABENTO_API_KEY`; A0_MVP spec requires Databento |

**Install to unblock the 17 skipped tests:**
```
pip install -e ".[dev]"      # pyarrow → parquet roundtrip tests
pip install -e ".[phase1]"   # ib_insync + databento → download tests
```

---

## Phase C — Alpha Gate Race 🟡

All alphas go through the **same locked gate**. No alpha gets primacy by assertion.

```
Gate thresholds (locked, immutable):
  n ≥ 200 net trades          net PF > 1.25        win rate > 45%
  Sharpe > 1.2                max DD < 15%          CPCV median PF > 1.0
  WF pass rate ≥ 60%          MC p5 PF > 0.9        DSR z-score > 0
```

### Alpha verdicts

```
 Alpha       Spec     Built    Gated    Verdict
 ─────────────────────────────────────────────────────────────────────────
 A0_MVP      ✅       ✅       ⬜       PENDING
             ⚠️  PLUMBING CHECK ONLY — verdict expected FRAGILE
             sweep+choch → entry = archived SMC_H1_FRAGILE pattern (GC PF 0.698)
             GROUND_TRUTH §3: SMC answers WHERE not WHEN; ChoCH→entry is WHEN
             Valid purpose: confirm pipeline runs; NOT a test of A1 hypothesis

 A1          ✅       ✅       ⬜       PENDING
             (full SMC WHERE-filter + momentum/delta WHEN-trigger)
             BLOCKED ON: A0_MVP plumbing run + Databento data

 A2          ✅       ✅       ✅       READ  ⚠️
             n=325 OOS · 10/11 PASS · DSR FAIL (z=−25.32)
             PF=3.745 · Sharpe=6.34 · DD=11.56%
             → not ROBUST; can only feed A3 ensemble

 A3          ✅       🟡       ⬜       PENDING  (needs A1 + A2 gated first)
             (ensemble: 0.4·A1 + 0.3·regime + 0.3·A2 > 0.75)
```

Optional additional hurdle (adopted): each alpha should **beat a simple trend-following baseline**
on the same data before promotion; the baseline and every variant are logged as DSR trials.

---

## Phase D — Execution Layer 🔒 LOCKED

> **Locked until at least one ROBUST verdict exists.** This is also verification PHASE 7
> (infrastructure resilience): API-down, DB-failure, VPS-reboot, net-outage, webhook-failure must
> all degrade to safe-mode with state recovery and no duplicate orders.

| Component | Status |
|-----------|--------|
| IB historical data (Phase B) | ✅ Built (`ag/data/ib_live/`) |
| Nautilus Trader integration | 🔒 Locked |
| IB live order gateway | 🔒 Locked |
| Order management / retry / kill switch | 🔒 Locked |
| Live position journal | 🔒 Locked |
| Resilience test suite (PHASE 7) | 🔒 Locked |

---

## Phase E — Live Trading 🔒 LOCKED

> Verification rungs 8 → 9 → 10 → 11, in order. Owner-only flip.

```
  ROBUST gate verdict
   └▶ PHASE 8  Paper / 30-day dry-run    (READY_FOR_PAPER)
        └▶ PHASE 9  Shadow trading 30d   (READY_FOR_SHADOW)
             └▶ PHASE 10 Live pilot      (READY_FOR_LIVE_PILOT — owner flips flag)
                  $100 → $250 → $500 → $1000, scale only on sustained edge
                  └▶ PHASE 11 Scale-up   (READY_FOR_SCALE — 10k/50k/100k sims stable)
```

---

## Risk Limits (locked, non-bypassable)

```
  Per trade:  0.5% account risk          Leverage: max 5×
  Daily:      2% loss limit              Concurrent positions: max 3
  Weekly:     6% loss limit              Drawdown: 15% max-from-peak
```

---

## Master Correction Loop (on any phase failure)

```
  Failure → Root-cause analysis → Code fix → Unit test → Integration test
          → Replay test → Re-run the failed phase.   Never skip back to live.
```

A FRAGILE alpha is archived to `research_archive/<alpha>/` with a verdict header — **not** tuned
to "pass." Tuning a rejected entry to flatter it is forbidden (`GROUND_TRUTH.md`).

---

## Final Production-Readiness Gate

Live capital is authorized only when **all** hold:

```
 ✓ Architecture verified            ✓ Risk controls verified (6 guards)
 ✓ Code quality clean (+mypy/bandit) ✓ Resilience/recovery tests pass
 ✓ Component tests pass              ✓ 30–60d paper (dry-run) complete
 ✓ Integration tests pass           ✓ 30d shadow trading complete
 ✓ Replay: no lookahead/repainting  ✓ ROBUST gate verdict on GC (net-of-cost)
 ✓ Backtest ROBUST (locked gate)    ✓ Live pilot profitable + monitoring active
 ✓ Kill switch operational          ✓ Audit/journal logs complete
 ✓ Owner manually enables live      ← the only hand on the switch
```

---

## What "done" looks like

```
  Phase B complete  →  GC 1m+1h data downloads, integrity checks pass, suite green
  A0_MVP run        →  plumbing confirmed (verdict expected FRAGILE — that's fine)
  A1 ROBUST         →  first real edge; A3 ensemble becomes buildable
  A3 / A1 ROBUST    →  PHASE 7 resilience + 30-day dry-run begin
  Dry-run + shadow  →  owner enables live pilot. Not before. Not the agent.
```

> Honest prior: "profitable SMC bot" is still **unproven** here. Pure-SMC entries are archived
> FRAGILE and A2 was demoted READ-not-ROBUST. This ladder is how we find out *cheaply* — and a
> well-evidenced "no edge" is a valid, successful outcome.
