# AG Auto-Trade — Live Roadmap
> Last synced: 2026-06-14 (A1_WHERE_ONLY lock spec created — PR #25 pending) · Source of truth: `docs/PROJECT_STATE.md`

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
 │     ✅ done (GC+6E 1h+1m cached)        ✅ done          🔒 D/E           │
 │                                                                           │
 │  ◀────────── GATE required before execution layer may be built ─────────▶│
 └──────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Progress

```
Phase A  Platform hardening     ████████████████████  100%  ✅ DONE  (audit 2026-06-14: PASS)
Phase B  Data layer             ████████████████████  100%  ✅ DONE (GC+6E 1h+1m 2020-2024)
Phase C  Alpha gate race        ████████░░░░░░░░░░░░   40%  🟡 A0 FRAGILE · A1_WHERE_ONLY lock pending PR #25
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
7. ✅ A1 BEGAN           A1 full WHERE filter ran (GC 5yr 33 trades, 6E artifact)
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
│  ⬅️  WAITING: PR #25 CI green → merge → gate run        │
│                                                         │
│  Pre-gate code audit (2026-06-14) finding:              │
│  A1SmcMomentum does NOT implement the locked §1 spec.   │
│  Built code = WHERE-only (no MT1/MT2/MT3, no Fib Z4,   │
│  no regime gate, no ATR floor). 5 numeric params were   │
│  not pre-committed.                                     │
│                                                         │
│  Owner decision: Option C                               │
│  → New alpha: A1_WHERE_ONLY                             │
│  → A1_WHERE_ONLY_DECISION.md locked (n_trials=23,       │
│    IS cutoff=2022-12-30, GC+6E CostModel pre-committed) │
│  → Full A1 §1 spec marked NOT BUILT — needs fresh       │
│    held-out window to gate validly                      │
│  → PR #25 open (lock/a1-where-only-spec)               │
│                                                         │
│  After PR #25 merges:                                   │
│  Run A1_WHERE_ONLY: GC+6E, 5yr, per §9, --n-trials 23  │
│  Expect FRAGILE on both (n≈33 GC < READ floor 50)       │
│  If FRAGILE on all → archive → A2 carries the race     │
└─────────────────────────────────────────────────────────┘
```

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
| Test suite: unit · integration · backtest · e2e | ✅ | **603 / 603 green** (replay suite added PR #13) |
| CI (GitHub Actions) + branch protection | ✅ | PR required + test check |
| Pipeline end-to-end verified (synthetic) | ✅ | Preflight 2026-06-14; 2 bugs fixed |
| Repo audit | ✅ | `docs/audits/REPO_AUDIT_2026-06-14.md` — PASS (4 WARNs open) |

---

## Phase B — Data Layer ✅ DONE

| Step | Status | Notes |
|------|--------|-------|
| B0 — IB loader (`IBHistoricalLoader`) | ✅ | Offline-first, CONTFUT, chunked pacing |
| B0 — Databento loader (`DatabentoLoader`) | ✅ | `stype_in=continuous` fix PR #18 |
| B0 — Source-agnostic factory (`get_loader`) | ✅ | Identical `.load()` API on both |
| B0 — CME roll calendar (`roll.py`) | ✅ | `get_front_month()` for GC/MGC/6E |
| B0 — Integrity checker (`check_ohlcv`) | ✅ | C1–C8, shared across both loaders |
| B0 — Synthetic fixtures + data tests | ✅ | All green (pyarrow + ib_insync installed) |
| B0 — Pipeline e2e verified (preflight) | ✅ | backtest → gate runs end-to-end |
| B1 — IB plumbing download | 🟡 OPTIONAL | READ-tier only; not gate-grade |
| B2 — Integrity check on downloaded data | ⬜ | Deferred — run before production use |
| B3 — GC 1m 2022-2024 | ✅ | 31,284 bars · `/home/aungp/data/cache/GC_1m.parquet` |
| B3 — GC 1h 2020-2024 | ✅ | 10,451 bars · `/home/aungp/data/cache/GC_1h.parquet` |
| B3 — 6E 1h 2020-2024 | ✅ | 24,441 bars · `/home/aungp/data/cache/6E_1h.parquet` |

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

 A1 (full spec) ✅     ❌       ⬜       NOT BUILT
             §1 (WHERE+WHEN, Z1–Z4, MT1–MT3) is the locked spec — never implemented.
             Requires a fresh held-out data window to gate validly.
             See: ag/validation/lock_before_look/A1_SMC_MOMENTUM_DECISION.md §8

 A1_WHERE_ONLY ✅     ✅       ⬜       LOCK PENDING  ← PR #25
             Built code: sweep+ChoCH+OB+FVG+displacement, no WHEN gate
             Backtest: GC 5yr 33 approved · WR 66.7%; 6E 5yr 3 (artifact)
             n_trials floor = 23 · IS cutoff = 2022-12-30 (pre-committed)
             Gate run pending PR #25 merge. Expect FRAGILE (n<50 READ floor)

 A2          ✅       ✅       ✅       READ  ⚠️
             n=325 OOS · 10/11 PASS · DSR FAIL (z=−25.32)
             PF=3.745 · Sharpe=6.34 · DD=11.56%
             → not ROBUST; can only feed A3 ensemble

 A3          ✅       🟡       ⬜       PENDING  (needs A1 + A2 gated first)
             (ensemble: 0.4·A1 + 0.3·regime + 0.3·A2 > 0.75)
```

### Phase C progress log

```
 DONE  A0_MVP (2026-06-14) — FRAGILE · 38 trades GC 1m 2022-24 · below floor
       Archive: research_archive/a0_mvp/VERDICT.md · 1 trial logged

 DONE  A1 code audit (2026-06-14) — spec ≠ implementation discovered
       A1SmcMomentum built = WHERE-only (no WHEN, no Fib Z4, no regime gate)
       5 numeric params unlogged. Owner decision: Option C (new alpha ID)

 DONE  A1_WHERE_ONLY lock spec created (2026-06-14) — PR #25 pending CI
       A1_WHERE_ONLY_DECISION.md: n_trials=23, IS cutoff=2022-12-30
       A1 §1 full spec marked NOT BUILT in amendment log

 NEXT  Merge PR #25 → run A1_WHERE_ONLY GC+6E 5yr --n-trials 23
       Expect FRAGILE → archive → A2 carries the race

 LAST  A3 ensemble gate — needs A1 + A2 both gated

 DISCIPLINE: every parameter tune logged in trial_log.jsonl BEFORE the run.
             --n-trials = line count per alpha in trial_log.jsonl at gate time.
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

| Gap | Priority | Status |
|-----|----------|--------|
| ~~`DATABENTO_API_KEY` not set~~ | ~~🔴 Critical~~ | ✅ CLOSED 2026-06-14 — key set, loader fixed |
| ~~FRAGILE header missing (S1)~~ | ~~🟡 High~~ | ✅ CLOSED — headers added, replay suite PR #13 |
| ~~`_active_obs` unbounded (S9)~~ | ~~🟡 High~~ | ✅ CLOSED — capped at 50 in `a1_alpha.py` |
| ~~`TRIALS.md` parameter ledger (S8)~~ | ~~🟡 Medium~~ | ✅ CLOSED — `trial_log.jsonl` + `ag/validation/trial_log.py` |
| ~~No look-ahead regression tests (S6)~~ | ~~🟡 Medium~~ | ✅ CLOSED — replay suite added PR #13 (603 tests) |
| ~~pyarrow not installed~~ | ~~Low~~ | ✅ CLOSED — installed |
| ~~ib_insync not installed~~ | ~~Low~~ | ✅ CLOSED — installed |
| No unit tests for cpcv/walk_forward/monte_carlo | Low | Open — deferred post-verdict |
| 6E stateful risk-engine artifact in multi-year backtests | 🟡 Medium | Open — early crash locks engine for full run; needs reset-per-year approach before 6E can be gated |

---

## What "done" looks like

```
  Phase B complete  ✅  GC+6E 1h+1m 2020-2024 cached, 603 tests green (2026-06-14)
  A0_MVP            ✅  FRAGILE — pipeline confirmed, archived (2026-06-14)
  A1 ROBUST         ⬜  First real gate verdict. Needs owner decision + possible trial 3.
  A2 ROBUST         ⬜  If A1 FRAGILE, A2 carries the race (currently READ n=325).
  A3 ROBUST         ⬜  Ensemble gate — needs A1 or A2 ROBUST first.
  30-day dry-run    ⬜  Starts after first ROBUST verdict.
  Live trading      ⬜  Owner manually enables — not before dry-run passes.
```
