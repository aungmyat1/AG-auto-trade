# AG Auto-Trade — Live Roadmap
> Last synced: 2026-06-13 · Source of truth: `docs/PROJECT_STATE.md`

---

## System Pipeline (end-to-end)

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                         SIGNAL PIPELINE                                  │
 │                                                                          │
 │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
 │  │   DATA   │───▶│  ALPHA   │───▶│   RISK   │───▶│ EXECUTE  │          │
 │  │ Databento│    │ propose()│    │ validate │    │  IB/Naut │          │
 │  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
 │      ⬜ B           🟡 C           ✅ done          ⬜ D                 │
 │   BLOCKED ◀────────────────── GATE required ───────────────────────▶   │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Progress

```
Phase A  Platform hardening     ████████████████████  100%  ✅ DONE
Phase B  Data layer             ░░░░░░░░░░░░░░░░░░░░    0%  🔴 BLOCKED
Phase C  Alpha gate race        ████░░░░░░░░░░░░░░░░   20%  🟡 IN PROGRESS
Phase D  Execution (IB/Naut)    ░░░░░░░░░░░░░░░░░░░░    0%  🔒 LOCKED
Phase E  Live trading           ░░░░░░░░░░░░░░░░░░░░    0%  🔒 LOCKED
```

---

## ══════════════ YOU ARE HERE ══════════════

```
┌─────────────────────────────────────────────────────┐
│  🔴  CURRENT BLOCKER                                │
│                                                     │
│  Databento API key not set.                         │
│  Every downstream step is gated behind real data.   │
│                                                     │
│  FIX:  Add DATABENTO_API_KEY to .env               │
│                                                     │
│  THEN: python3 scripts/run_alpha_backtest.py \      │
│          --alpha a0_mvp --data <gc.parquet>        │
│        python3 scripts/run_gate.py trades.csv \     │
│          --instrument GC --n-trials 1             │
└─────────────────────────────────────────────────────┘
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
| Test suite: unit · integration · backtest · e2e | ✅ | **392 / 392 green** |
| CI (GitHub Actions) + branch protection | ✅ | PR required + test check |

---

## Phase B — Data Layer 🔴 BLOCKED

> **Unblocks everything downstream. This is the critical path.**

| Step | Status | Action |
|------|--------|--------|
| B0 | 🔴 BLOCKED | Get Databento API key → `DATABENTO_API_KEY` in `.env` |
| B1 | ⬜ Pending | Build `ag/data/databento/loader.py` — OHLCV 1m+1h GC/MGC/6E, parquet cache |
| B2 | ⬜ Pending | Continuous-contract roll policy (volume-crossover, back-adjusted) |
| B3 | ⬜ Pending | `ag/data/databento/integrity.py` — gap / duplicate / session checks |
| B4 | ⬜ Pending | Offline fixture bundle so CI stays network-free |

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

 A1          ✅       ✅       ⬜       PENDING
             (full SMC filter: sweep+choch+OB+FVG+displacement)

 A2          ✅       ✅       ✅       READ  ⚠️
             n=325 OOS · 10/11 PASS · DSR FAIL (z=−25.32)
             PF=3.745 · Sharpe=6.34 · DD=11.56%
             → not ROBUST; can only feed A3 ensemble

 A3          ✅       🟡       ⬜       PENDING  (needs A1 + A2 gated first)
             (ensemble: 0.4·A1 + 0.3·regime + 0.3·A2 > 0.75)
```

### Next actions in Phase C (after B0 unblocked)

```
 1. A0_MVP backtest  → scripts/run_alpha_backtest.py --alpha a0_mvp --data <gc.parquet>
 2. A0_MVP gate      → scripts/run_gate.py trades.csv --instrument GC --n-trials 1
 3. Check signal rate ≥ 1 trade per 20 bars (if not → lower swing_lookback, new trial)
 4. If ROBUST → add one filter at a time (each = new alpha ID + new DECISION.md)
 5. A1 full config gate
 6. A3 ensemble gate (last)
```

---

## Phase D — Execution Layer 🔒 LOCKED

> **Locked until at least one ROBUST verdict exists. Not started. Not planned.**

| Component | Status |
|-----------|--------|
| Nautilus Trader integration | 🔒 Locked |
| Interactive Brokers gateway | 🔒 Locked |
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
| **Databento API key** | 🔴 Critical — blocks everything |
| CPCV/WF train-side purge scores only OOS | Low — by design |
| Gate threshold file loader (hardcoded in gate.py) | Low |

---

## What "done" looks like

```
  Phase B complete  →  GC 1m+1h data loads offline, integrity checks pass
  A0_MVP ROBUST     →  First real gate verdict. A1 filter-by-filter work begins.
  A1 ROBUST         →  A3 ensemble becomes buildable.
  A3 ROBUST         →  30-day dry-run starts. Execution layer build begins.
  Dry-run pass      →  Owner enables live trading. Not before.
```
