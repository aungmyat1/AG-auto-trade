# AG Auto-Trade — Live Roadmap
> Last synced: 2026-06-14 · Source of truth: `docs/PROJECT_STATE.md`

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
Phase A  Platform hardening     ████████████████████  100%  ✅ DONE  (audit 2026-06-14: PASS)
Phase B  Data layer             ████████████████████  100%  ✅ DONE (GC 1m cached 2022-2024)
Phase C  Alpha gate race        █████░░░░░░░░░░░░░░░   25%  🟡 A0_MVP FRAGILE · A1 NEXT
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

### Rule 2 — Fallback Path (futures-only; crypto is a closed door)

Primary — and only approved — research universe: **GC · MGC · 6E** (CME futures),
per-instrument models, GC primary.

If A1 fails to achieve ROBUST on the primary universe, the approved fallbacks are,
in order, **on the same futures universe**:

1. **A2** (master-trader copy) — currently READ; race it net-of-cost in its own right.
2. **A3** (ensemble: A1 × regime × A2) — once its components are gated.
3. **More futures data** — full multi-year GC + MGC + 6E to lift trade count toward the
   n≥50 floor / n≥200 ROBUST. The n problem is fixed by data, **never by loosening a filter**.

If A1/A2/A3 are **all** FRAGILE or uneconomic on futures, that is a valid "no edge" result —
stop, do not tune-to-fit. Any venue reconsideration after that is a separate, evidence-gated,
owner-only decision, and **crypto is NOT the default successor**: crypto-SMC carries its own
FRAGILE verdict and the Bybit pivot was rejected on corrected facts
(`research_archive/rejected_bybit_pivot_v5/`). Crypto is a closed door, not plan B.

---

## ✅ FREEZE LIFTED — A0_MVP FRAGILE verdict recorded (2026-06-14)

**Freeze sequence — COMPLETE (2026-06-14):**

```
1. ✅ Preflight audit     DONE 2026-06-14 — 2 pipeline bugs fixed, audit clean
2. ✅ Acquire Databento   DONE 2026-06-14 — key set, loader fixed (stype_in=continuous)
3. ✅ Download GC data    DONE — 31,284 bars 2022-01-03→2024-12-30 cached
4. ✅ Run A0_MVP          DONE — 38 trades, WR 47.4%, mean R −0.003
5. ✅ Run gate            SKIPPED — 38 < 50 (below READ floor); gate cannot run on n<50
6. ✅ Record verdict      DONE — FRAGILE, research_archive/a0_mvp/VERDICT.md
7. ⬅️ OWNER REVIEW        Review A0_MVP result → FREEZE fully lifts → A1 begins  ← YOU ARE HERE
```

**Still frozen until A1 ROBUST verdict (Rule 1 — no new systems before first ROBUST verdict):**

| Item | Why frozen |
|---|---|
| Crypto / Bybit (BTC-ETH) | **CLOSED door** — rejected on corrected facts, not a gated hedge (`research_archive/rejected_bybit_pivot_v5/`) |
| New SMC filters beyond A1 spec | Rule 1 — each filter = new alpha ID, must gate A1 first |
| Master-trader selector enhancements | Rule 1 — A2 is READ; no tuning before gate race |
| A3 ensemble build | Requires A1 + A2 both gated |
| Execution layer (Nautilus/IB) | Phase D locked until ROBUST verdict exists |

---

## ══════════════ YOU ARE HERE ══════════════

```
┌─────────────────────────────────────────────────────────┐
│  ✅  FREEZE LIFTED — A0_MVP FRAGILE (2026-06-14)        │
│                                                         │
│  A0_MVP result:                                         │
│    38 approved trades on GC 1m 2022-2024                │
│    Win rate 47.4%  |  Mean R −0.003                     │
│    Below READ floor (n<50) — gate skipped               │
│    Verdict: FRAGILE (expected — pipeline smoke test)     │
│    Archive: research_archive/a0_mvp/VERDICT.md          │
│                                                         │
│  All 4 audit items confirmed closed (S1/S6/S8/S9).     │
│  557/557 tests green.                                   │
│                                                         │
│  ⬅️  OWNER: review A0_MVP result, then give go-ahead    │
│                                                         │
│  After review — A1 sequence:                            │
│  1. Resample 1m → 1h (python3, ~5s)                    │
│  2. Log A1 trial in trial_log.py                        │
│  3. scripts/run_alpha_backtest.py --alpha a1 \          │
│         --data /home/aungp/data/cache/GC_1h.parquet \  │
│         --instrument GC --out results/a1_trades.csv     │
│  4. scripts/run_gate.py results/a1_trades.csv \         │
│         --instrument GC --cost-preset gc --n-trials <N> │
│  5. Record verdict → owner reviews                      │
└─────────────────────────────────────────────────────────┘
```

> **A1 selectivity guard (read before running A1).** A0_MVP fired 3,533 signals at an 11%
> rate (1 in 9 bars); the G3 cooldown blocked 99%, leaving n=38. That low count is the full
> WHERE filter **doing its job** — A1 (OB + FVG + displacement, on 1h) is *meant* to be
> selective. So: if A1's n falls below the floor, **the fix is more data — full multi-year
> GC + MGC + 6E — never a looser filter.** Loosening to manufacture trades re-introduces the
> over-firing A0_MVP failure mode and inflates the DSR trial count. Selectivity is the signal,
> not the bug.

---

## Phase A — Platform & Validation Core ✅ (audited 2026-06-14)

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
| Test suite: unit · integration · backtest · e2e | ✅ | **540 / 540 green** (17 skip pending deps) |
| CI (GitHub Actions) + branch protection | ✅ | PR required + test check |
| Pipeline end-to-end verified (synthetic) | ✅ | Preflight 2026-06-14; 2 bugs fixed |
| Repo audit | ✅ | `docs/audits/REPO_AUDIT_2026-06-14.md` — PASS (4 WARNs open) |

---

## Phase B — Data Layer 🟡 DATABENTO KEY NEEDED

> **Loaders built + pipeline verified end-to-end. Single remaining blocker: Databento API key.**

| Step | Status | Notes |
|------|--------|-------|
| B0 — IB loader (`IBHistoricalLoader`) | ✅ | Offline-first, CONTFUT, chunked pacing |
| B0 — Databento loader (`DatabentoLoader`) | ✅ | Offline-first, lazy import, parquet cache |
| B0 — Source-agnostic factory (`get_loader`) | ✅ | Identical `.load()` API on both — one flag to switch |
| B0 — CME roll calendar (`roll.py`) | ✅ | `get_front_month()` for GC/MGC/6E |
| B0 — Integrity checker (`check_ohlcv`) | ✅ | C1–C8, shared across both loaders |
| B0 — Synthetic fixtures + 99 data tests | ✅ | 82 pass · 17 skip (pyarrow/ib_insync absent) |
| B0 — Pipeline e2e verified (preflight) | ✅ | backtest → gate runs on synthetic; 2 bugs fixed |
| B1 — IB plumbing download | 🟡 OPTIONAL | READ-tier only (1 yr, 1 regime); not gate-grade |
| B2 — Integrity check on downloaded data | ⬜ | Auto after download |
| **B3 — Databento 1m bars (gate-grade)** | 🔴 **BLOCKED** | Needs `DATABENTO_API_KEY` → **only remaining blocker** |

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
 A0_MVP      ✅       ✅       ✅       FRAGILE  (2026-06-14)
             38 approved trades on GC 1m 2022-2024 — below READ floor (n<50)
             Gate skipped. Archived: research_archive/a0_mvp/VERDICT.md
             Purpose fulfilled: pipeline confirmed end-to-end.

 A1          ✅       ✅       ⬜       PENDING  ← NEXT
             (full SMC filter: sweep+choch+OB+FVG+displacement)
             Run on GC 1h — owner review of A0_MVP result required first

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

| Gap | Priority | Source |
|-----|----------|--------|
| **`DATABENTO_API_KEY` not set** | 🔴 Critical — only blocker to first verdict | B3 |
| FRAGILE header missing from SMC detector files | 🟡 High — fix before gate (audit S1 FAIL) | Audit 2026-06-14 |
| `_active_obs` unbounded growth in `a1_alpha.py` | 🟡 High — memory risk on real data (audit S9) | Audit 2026-06-14 |
| `TRIALS.md` parameter ledger missing | 🟡 Medium — required by SMC skill (audit S8) | Audit 2026-06-14 |
| No look-ahead regression tests per SMC detector | 🟡 Medium — audit S6 | Audit 2026-06-14 |
| pyarrow not installed | Low — `pip install -e ".[dev]"` → 17 tests green | B0 |
| ib_insync not installed | Low — `pip install -e ".[phase1]"` | B1 |
| No unit tests for cpcv/walk_forward/monte_carlo | Low — deferred post-verdict | Audit R7 |
| CPCV/WF train-side purge scores only OOS | Low — by design | - |

---

## What "done" looks like

```
  Phase B complete  →  GC 1m+1h data downloads, integrity checks pass, 540+17 all green
  A0_MVP ROBUST     →  First real gate verdict. A1 filter-by-filter work begins.
  A1 ROBUST         →  A3 ensemble becomes buildable.
  A3 ROBUST         →  30-day dry-run starts. Execution layer build begins.
  Dry-run pass      →  Owner enables live trading. Not before.
```
