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

## ══════════════ YOU ARE HERE ══════════════

```
┌─────────────────────────────────────────────────────────┐
│  🟡  CURRENT TASK — first IB data download              │
│                                                         │
│  Data layer is built. One step away from real data.     │
│                                                         │
│  1. pip install -e ".[dev]" && pip install ib_insync    │
│  2. Start TWS or IB Gateway (paper account fine)        │
│  3. Copy .env.ib.example → .env, set IB_PORT            │
│  4. Pull first bars:                                    │
│       from ag.data.loader import get_loader             │
│       loader = get_loader("ib")                         │
│       df = loader.load("GC","1h",                       │
│              start="2024-01-01",end="2024-12-31")        │
│                                                         │
│  THEN: run A0_MVP backtest → gate                       │
│    scripts/run_alpha_backtest.py --alpha a0_mvp         │
│    scripts/run_gate.py trades.csv --instrument GC \     │
│      --n-trials 1                                       │
│                                                         │
│  Databento upgrade path (when deeper history needed):   │
│    Add DATABENTO_API_KEY to .env                        │
│    Switch get_loader("databento") — same alpha code     │
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
| **B1 — First real download** | 🟡 **NEXT** | Start TWS → `loader.load("GC","1h",start=…)` |
| B2 — Integrity check on live data | ⬜ | `check_ohlcv(df,"GC","1h")` — auto after download |
| B3 — Pull 1m bars for A0_MVP backtest | ⬜ | ~180D chunks, loader handles pacing |

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
 A0_MVP      ✅       ✅       ⬜       PENDING  ← run this first
             (sweep+choch only — minimum viable path to first real verdict)
             BLOCKED ON: real GC 1m data

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

### Next actions in Phase C (after first data download)

```
 1. A0_MVP backtest  → scripts/run_alpha_backtest.py --alpha a0_mvp --data <gc_1m.parquet>
 2. Check signal rate ≥ 1 trade per 20 bars (if not → lower swing_lookback, new trial)
 3. A0_MVP gate      → scripts/run_gate.py trades.csv --instrument GC --n-trials 1
 4. If ROBUST → add one filter at a time (each = new alpha ID + new DECISION.md)
 5. A1 full config gate
 6. A3 ensemble gate (last)
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
