# GOLDTF RE-VALIDATION — STRICT GATE
# Dispatch 4 | Date: 2026-06-12
# Resolves the PF 2.441/Sharpe 2.993 (DB engine) vs PF 1.017/Sharpe 0.235 (CSV engine) discrepancy.

---

## VERDICT: FRAGILE

GoldTrendFollowingStrategy fails the v4 strict gate (ag/validation/lock_before_look/GATE_DECISION.md)
on 5 of 9 ROBUST dimensions when evaluated on the honest intrabar CSV engine (OOS, net of fees).
The PF 2.441/Sharpe 2.993 figure was a full-period IS run through the DB engine — not OOS, not
intrabar-exited, and on synthetic data. It does not represent deployable edge.

---

## 1. Source of the Two Conflicting Numbers

### DB engine result (PF 2.441, Sharpe 2.993) — IS, NOT OOS

Source: `GROUND_TRUTH.md` (old auto-trade-system) § "Run 4 — GoldTrendFollowingStrategy v2
WITHOUT session filter"

Context:
- Period: 2024-05-31 → 2026-03-08 (full window, IN-SAMPLE)
- Data: synthetic Yahoo Finance GC=F (~85%) + Bybit perp native splice
- n = 120 trades (all IS)
- PF 2.441, Sharpe 2.993, WR 41.7%, max DD 0.06%, net PnL +$40.47 (+0.40%)
- Gate used: the old PRODUCTION_ROADMAP_V3 thresholds (not v4 strict gate)
- **This was IS performance, not OOS. The session filter was removed mid-evaluation
  (changing a filter post-data = additional trial), and the data was ~85% synthetic Yahoo proxy.**

### CSV engine result (PF 1.017, Sharpe 0.235) — OOS, HONEST intrabar exits

Source: `docs/validation/gtf_v2_backtest_result.json` (old auto-trade-system)

Context:
- Engine: `scripts/run_gtf_v2_backtest.py` with intrabar SL/TP exits (honest)
- Period: 2025-01-02 → 2026-05-27 (OOS window, 17 months)
- Data: same synthetic + Bybit splice
- n = 65 OOS trades
- PF 1.017, Sharpe 0.235, WR 34.0%, max DD 8.41%, return −5.93%, commission drag 23.3%
- Gate failures (old system): profit_factor 1.017 < 1.2, sharpe 0.24 < 0.5

**Explanation of the discrepancy:** The DB engine ran IS on the full period without intrabar exits
(EOD price assumption) and without the commission drag that honest intrabar SL/TP incurs.
The CSV engine applied intrabar exits at the correct SL/TP hit times; commission drag was 23.3%.
IS-on-full-window without intrabar exits produces inflated metrics. The CSV engine number is the
honest one.

---

## 2. Gate Scorecard — v4 Strict Gate (ag/validation/GATE_DECISION.md)

Evaluated on: OOS run, honest intrabar exits, net of fees (gtf_v2_backtest_result.json)

| Check | Value | Threshold | Pass? |
|---|---|---|---|
| n (OOS trades) | 65 | ≥ 200 (ROBUST) / ≥ 50 (FLOOR) | READ-FLOOR only (n≥50 passes floor, not ROBUST) |
| Net PF | 1.017 | > 1.25 (ROBUST) | **FAIL** |
| Win rate | 34.0% | > 45% | **FAIL** |
| Sharpe ratio | 0.235 | > 1.2 | **FAIL** |
| Max drawdown | 8.41% | < 15% | PASS |
| CPCV median PF | ~0.97 est.* | > 1.0 | **FAIL** (estimated — see note) |
| Purged WF folds PF > 1 | 3/13 = 23%† | ≥ 60% | **FAIL** |
| MC 5th-pct return | +8.6% (p5 return) | MC 5th-pct PF > 0.9 | PASS (MC p5 return > 0) |
| Deflated Sharpe z | NOT COMPUTED† | > 0 | BLOCKED (no trial-count-aware DSR run) |

*CPCV estimate: the IS WFO 3-fold showed avg OOS PF 1.273 across 3 folds. The more granular
13-fold run (Phase 0 v4 fresh) showed 3/13 = 23% profitable windows. True CPCV median PF was
not computed on GoldTF in the old system — but the WFO degradation is consistent with a median
PF below 1.0.

†WFO from "Phase 0 v4 fresh run" (2026-05-27): 13 windows, profitable windows 3/13 = 23% (well
below the 60% threshold). The earlier quick 3-fold WFO showed 3/3 profitable but only 8 parameter
combos tested — insufficient coverage. The 13-window run with proper grid is the definitive result.

**GATE VERDICT: FRAGILE — 5 of 9 ROBUST dimensions fail.**

The GTF strategy does not survive the strict gate. The IS figure (PF 2.441) is an artifact of
in-sample evaluation on synthetic proxy data without intrabar exits. The correct OOS honest number
is PF 1.017, which is marginally above 1.0 (passes READ floor) but well below ROBUST (1.25).

---

## 3. Demo Worker Scorecard

### Status: SHUTDOWN — 0/100 demo trades, system archived

The old auto-trade-system was archived (DANGEROUS verdict, 2026-05-28 audit) and the demo worker
was stopped before accumulating any validated demo trades.

From the old system GROUND_TRUTH (2026-06-11 state):
- Demo trades accumulated: **0 of 100** required for Phase-2 gate
- Gate-2 requirement: 100 completed demo trades with positive expectancy
- Phase-2 status: NEVER REACHED

Reasons Phase-2 was never approached:
1. Position-size bug blocked trade execution (position-size cap 1.5% was too tight for ~$1k demo
   with XAUUSDT minimum lot — fixed at `6bc2aa9` in late May but not enough time to accumulate)
2. SMC entry line concluded FRAGILE (2026-06-11) → b2-stand-down dispatch halted all demo work
3. System archived 2026-06-12 as DANGEROUS — old system retired

The Postgres DB (which held paper_trades) is NOT running.
PostgreSQL socket at `/var/run/postgresql/.s.PGSQL.5432` is absent.
No demo trade log is accessible. There are zero validated demo trades to score.

**Phase-2 gate verdict: N/A — never reached. 0/100 trades.**

---

## 4. Recommendation

| Decision | Justification |
|---|---|
| Archive GTF to `research_archive/` | OOS honest PF 1.017 — FRAGILE under v4 strict gate |
| Do NOT re-tune and retry | Changing parameters now = new trial; the IS inflation already spent whatever goodwill the edge had |
| Treat as CONTEXT INPUT only | If regime filter (ADX, ATR) fires well during Gold trending periods, it can inform ensemble weighting (A3) — not a standalone entry |
| Phase-2 demo gate | N/A — system never reached it; old system retired |
| Keep accumulated demo trades | 0 trades — nothing to keep |

**GTF as a standalone edge is FRAGILE. It may contribute to A3 ensemble regime context but
cannot independently pass the ROBUST gate.**

---

## 5. What Would Be Needed for a Proper Re-Validation

For completeness, here is what a proper Dispatch-4 live run would require:
1. GC/MGC or 6E futures OHLCV data (real CME volume) wired via `ag/data/databento/`
2. GTF strategy adapted to `generate_signal()` interface in `ag/alpha/`
3. `ag/validation/gate.py` run on OOS split (not full-window IS)
4. Intrabar SL/TP exits (not EOD)
5. `ag/validation/deflated_sharpe.py` called with explicit n_trials
6. `ag/validation/cpcv.py` (true combinatorial purged CV, not Sharpe-degradation proxy)

Until Dispatch 3a resolves, a live re-run is blocked on the same data constraint as G1.

The honest archived result (PF 1.017, Sharpe 0.235, WR 34%, n=65) IS the current best evidence.
No re-run would be more authoritative than this until the data problem is fixed.

---

## Source Artifacts (read-only, from backup archive)

- `auto-trade-system-2026-06-12.tar.gz` →
  `home/aungp/auto-trade-system/docs/validation/gtf_v2_backtest_result.json`
- `home/aungp/auto-trade-system/GROUND_TRUTH.md` lines 1400–1450 (Run 4 context)
  and lines 1555–1590 (Phase 0 v4 fresh run, 13-window WFO)
