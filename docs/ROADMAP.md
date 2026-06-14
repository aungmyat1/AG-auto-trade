# AG Auto-Trade — Live Roadmap
> Last synced: 2026-06-13 · Source of truth: `docs/PROJECT_STATE.md`

---

## System Pipeline (end-to-end)

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                          SIGNAL PIPELINE                                  │
 │                                                                           │
 │  ┌──────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
 │  │     DATA     │───▶│  ALPHA   │───▶│   RISK   │───▶│ EXECUTE  │       │
 │  │  IB (MVP)    │    │ propose()│    │ validate │    │  IB/Naut │       │
 │  │  Databento ↑ │    │          │    │          │    │          │       │
 │  └──────────────┘    └──────────┘    └──────────┘    └──────────┘       │
 │     🟡 B  ←  first download pending    ✅ done          🔒 D/E           │
 │                                                                           │
 │  ◀────────── GATE required before execution layer may be built ─────────▶│
 └──────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Progress

```
Phase A  Platform hardening     ████████████████████  100%  ✅ DONE
Phase B  Data layer             ████████████████░░░░   80%  🟡 FIRST DOWNLOAD PENDING
Phase C  Alpha gate race        ████░░░░░░░░░░░░░░░░   20%  🟡 WAITING ON DATA
Phase D  Execution (IB/Naut)    ░░░░░░░░░░░░░░░░░░░░    0%  🔒 LOCKED
Phase E  Live trading           ░░░░░░░░░░░░░░░░░░░░    0%  🔒 LOCKED
```

---

## Standing Rules (locked — do not relax without owner approval)

### Rule 1 — First Verdict Rule

The project SHALL NOT introduce new trading infrastructure, exchanges, execution venues,
alpha frameworks, AI layers, master-trader systems, or instrument universes before the
first registered gate verdict is produced on real market data.

**Allowed before first verdict:** data acquisition · integrity validation · bug fixes ·
test maintenance · A0_MVP execution · gate execution · documentation updates.

**Not allowed before first verdict:** new alphas · new exchanges · new copy-trading systems ·
new SMC variants · new master-trader intelligence · new instruments.

The purpose: prevent scope expansion before evidence exists.

### Rule 2 — Instrument Escalation Path

Primary research instruments: **GC · MGC · 6E** (CME futures).

These remain the only approved research universe until a real gate verdict exists.

If A0_MVP and subsequent alphas fail to achieve ROBUST on the primary universe,
the next approved expansion path is:

1. BTCUSD
2. ETHUSD

Objective: faster hypothesis testing and higher signal frequency — not replacement of
the primary universe. No BTC/ETH infrastructure work begins before the first real verdict
on the primary universe unless explicitly approved by the owner.

---

## 🧊 DEVELOPMENT FREEZE — active until first verdict is reviewed

**The 7-step sequence to first verdict (clock starts when Databento key lands):**

```
1. Preflight audit        /audit-repo + /smc-review  (can run now — no key needed)
2. Acquire Databento      Owner action — add DATABENTO_API_KEY to .env
3. Download GC data       get_loader("databento").load("GC","1m","2022-01-01","2024-12-31")
4. Run A0_MVP             scripts/run_alpha_backtest.py --alpha a0_mvp --data <file>
5. Run gate               scripts/run_gate.py trades.csv --instrument GC --n-trials <N>
6. Record verdict         FRAGILE → research_archive/a0_mvp/   READ/ROBUST → PROJECT_STATE.md
7. FREEZE & REVIEW        Owner reviews the verdict before ANY further build.
```

**Do NOT start before step 7 is complete:**

| Item | Why frozen |
|---|---|
| BTC/ETH expansion | Rule 2 — no BTC/ETH work before first GC/6E verdict |
| New SMC filters | Rule 1 — A0_MVP must be gated first; each filter = new alpha ID |
| Master-trader selector enhancements | Rule 1 — A2 is READ; no tuning before gate race |
| Copy-trading optimizer | Rule 1 — no new systems before first verdict |
| AI signal ranking | Rule 1 — validation before optimization (CLAUDE.md §7) |

**The freeze is active now.** Step 2 (Databento key) is the only unblocked action.

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
│    → each tune = +1 to --n-trials (no exceptions)      │
│    scripts/run_gate.py trades.csv --instrument GC \     │
│      --n-trials <honest count from trial_log>           │
└─────────────────────────────────────────────────────────┘
```

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
| Test suite: unit · integration · backtest · e2e | ✅ | **498 / 498 green** (17 skip pending deps) |
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
| B0 — Synthetic fixtures + 99 data tests | ✅ | 82 pass · 17 skip (pyarrow/ib_insync absent) |
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
             CLAUDE.md §3: SMC answers WHERE not WHEN; ChoCH→entry is WHEN
             Valid purpose: confirm pipeline runs; NOT a test of A1 hypothesis
             BLOCKED ON: Databento 1m data (A0_MVP_DECISION.md spec)

 A1          ✅       ✅       ⬜       PENDING
             (full SMC filter: sweep+choch+OB+FVG+displacement)
             BLOCKED ON: A0_MVP gated first

 A2          ✅       ✅       ✅       READ  ⚠️
             n=325 OOS · 10/11 PASS · DSR FAIL (z=−25.32)
             PF=3.745 · Sharpe=6.34 · DD=11.56%
             → not ROBUST; can only feed A3 ensemble

 A3          ✅       🟡       ⬜       PENDING  (needs A1 + A2 gated first)
             (ensemble: 0.4·A1 + 0.3·regime + 0.3·A2 > 0.75)
```

### Next actions in Phase C (after Databento data lands)

```
 DISCIPLINE: every parameter tune must be logged in trial_log.py BEFORE the run.
             --n-trials = row count in trial_log.py at gate time. No exceptions.
             Unlogged experiment = self-deception (CLAUDE.md §7).

 1. A0_MVP backtest  → scripts/run_alpha_backtest.py --alpha a0_mvp --data <gc_1m.parquet>
    → A0_MVP is a pipeline smoke test; sweep+choch = archived FRAGILE; expect FRAGILE
    → If FRAGILE: archive to research_archive/a0_mvp/ — do NOT tune the signal to "fix" it
    → If signal rate < 1/20 bars: log tune attempt in trial_log.py, lower swing_lookback
    → Each lookback variant = +1 trial in --n-trials

 2. A0_MVP gate      → scripts/run_gate.py trades.csv --instrument GC \
                         --n-trials <count from trial_log.py>
    → IB 1h data is READ-tier only (1 year, 1 regime) — not valid for ROBUST verdict
    → Databento multi-year 1m data required for CPCV/WF to be meaningful

 3. A1 gate (first real edge test — WHERE filter + WHEN trigger, not ChoCH→entry)
 4. A3 ensemble gate (last — needs A1 + A2 both gated)
```

---

## Phase D — Execution Layer 🔒 LOCKED

> **Locked until at least one ROBUST verdict exists. IB historical data layer exists (Phase B)
> but the execution / order-management layer must not be built until the gate passes.**

| Component | Status |
|-----------|--------|
| IB historical data (Phase B) | ✅ Built (`ag/data/ib_live/`) |
| Nautilus Trader integration | 🔒 Locked |
| IB live order gateway | 🔒 Locked |
| Order management / retry logic | 🔒 Locked |
| Live position journal | 🔒 Locked |

---

## Phase E — Live Trading 🔒 LOCKED

> **Gate → ROBUST → 30-day dry-run → owner manually flips the live flag. Not the agent. Ever.**

```
  ROBUST verdict                 ─┐
  + 30-day dry-run pass          ─┤──▶  Owner enables live trading manually
  + owner explicit authorization ─┘
```

---

## Risk Limits (locked, non-bypassable)

```
  Per trade:  0.5% account risk          Leverage: max 5×
  Daily:      2% loss limit              Concurrent positions: max 3
  Weekly:     6% loss limit              Drawdown: 15% max-from-peak
```

---

## Open Gaps

| Gap | Priority |
|-----|----------|
| **First IB data download** | 🟡 High — unblocks A0_MVP gate |
| pyarrow not installed | Medium — `pip install -e ".[dev]"` → 17 tests go green |
| ib_insync not installed | Medium — `pip install -e ".[phase1]"` |
| CPCV/WF train-side purge scores only OOS | Low — by design |
| Gate threshold file loader (hardcoded in gate.py) | Low |

---

## What "done" looks like

```
  Phase B complete  →  GC 1m+1h data downloads, integrity checks pass, 498+17 all green
  A0_MVP ROBUST     →  First real gate verdict. A1 filter-by-filter work begins.
  A1 ROBUST         →  A3 ensemble becomes buildable.
  A3 ROBUST         →  30-day dry-run starts. Execution layer build begins.
  Dry-run pass      →  Owner enables live trading. Not before.
```
