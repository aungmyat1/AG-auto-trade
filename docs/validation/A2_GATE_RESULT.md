# A2 GATE RESULT — MASTER TRADER COPY
# Dispatch 3 | Run date: 2026-06-12
# Engine: ag/validation/ v4 stack (gate.py, cpcv.py, walk_forward.py, monte_carlo.py, deflated_sharpe.py)
# Gate spec locked BEFORE this run: ag/validation/lock_before_look/A2_MASTER_TRADER_DECISION.md

---

## VERDICT: READ (OPTIMISTIC)

**10/11 checks pass. 1 check fails (DSR).** A2 demonstrates a real edge at the per-
metric level but does not survive multiple-testing correction (Deflated Sharpe z < 0).

**NOT deployable standalone.** Contributes to A3 ensemble as the `0.3 × master_trader` term.

SURVIVORSHIP QUALIFIER: This verdict is labeled **OPTIMISTIC** — the visible universe
excludes traders delisted before the June 2026 scrape window. See §0 of the decision doc.

---

## Gate Input

| Parameter | Value |
|---|---|
| Trader UID | 279689 (TradingBridgeGold Forex Signals) |
| Total trades | 525 |
| IS window | trades 1–200 (cutoff: 2025-07-31T13:58:00+00:00) |
| OOS window | trades 201–525 (n=325, start: 2025-07-31T13:59:00+00:00) |
| Reference pip | 1.3050 $/oz (IS median \|exit−entry\|) |
| Cost per trade | 0.1149R (1.5 pips × $0.10/oz / 1.305) |
| n_trials | 11 (locked floor per §4 of decision doc) |
| Engine | ag/validation/ v4 stack |

---

## Scorecard (OOS, n=325)

| Check | Value | Threshold | Result |
|---|---|---|---|
| n ≥ 50 | 325 | ≥ 50 | **PASS** |
| gross PF > 1.0 | 4.23 | > 1.0 | **PASS** |
| n ≥ 200 | 325 | ≥ 200 | **PASS** |
| net PF > 1.25 | 3.745 | > 1.25 | **PASS** |
| win rate > 45% | 77.85% | > 45% | **PASS** |
| Sharpe > 1.2 | 6.34 | > 1.2 | **PASS** |
| max DD < 15% | 11.56% | < 15% | **PASS** |
| CPCV median PF > 1.0 | 3.719 | > 1.0 | **PASS** (10/10 folds above 1) |
| WF pass rate ≥ 60% | 100% | ≥ 60% | **PASS** (5-fold purged WF) |
| MC 5th-pct PF > 0.9 | 3.745 | > 0.9 | **PASS** (10k shuffles, seed 42) |
| DSR z > 0 (n_trials=11) | −25.32 | > 0.0 | **FAIL** |

---

## DSR Failure — Analysis

The Deflated Sharpe z-score is −25.32, far below the 0 threshold.

**Cause**: DSR (Bailey & López de Prado 2014) deflates the observed Sharpe by the expected
maximum Sharpe from `n_trials` independent trials. Even though the annualized Sharpe is 6.34,
the **per-trade Sharpe** (mean/stdev of R-multiples, without √252 scaling) is small because the
R-multiple distribution has high variance relative to its mean:

- Per-trade SR = mean(R) / stdev(R) ≈ 0.40
- E[max SR from 11 trials] >> 0.40 → z << 0

This is correct gate behavior. A strategy that survived 11 independent parameter choices would be
expected to show SR > 0.40 by chance alone. The edge at the annualized scale does not survive the
multiple-testing correction at the per-trade scale.

**This does NOT mean A2 has no edge.** The net PF=3.745, Sharpe=6.34, and CPCV/MC all confirm
a real directional edge. The DSR failure indicates the signal level (per trade) is not separately
robust from the selection process. This is consistent with a copy-trading strategy where the
"alpha" is the master's track record selection rather than an independent signal.

---

## Trial Count Log

| DoF | Count |
|---|---|
| Min trades filter (200) | 1 |
| Min track length (365d) | 1 |
| Martingale filter | 1 |
| Max DD filter (20%) | 1 |
| PF filter (≥1.5) | 1 |
| WR filter (≥55%) | 1 |
| Composite score weights | 1 |
| IS/OOS split cutoff (200th trade) | 1 |
| Copy lag (30s) | 1 |
| Slippage assumption (0.5 pip) | 1 |
| Commission (1.0 pip RT) | 1 |
| **Total n_trials** | **11** |

No sweeps or grid searches were run. No OOS metrics were observed before this run.
Lock-before-look protocol followed: decision doc committed before gate execution.

---

## Survivorship Bias Note

The SignalStart universe used for master selection contains recently-delisted traders but
NOT historically-delisted traders (failures before the June 2026 scrape window are invisible).

The PF=3.745 and other metrics reflect performance of a master selected from this biased universe.
In a universe that included all historical failures, the same selection criteria would likely
produce a lower-quality candidate. Verdicts are labeled OPTIMISTIC accordingly.

This does not change the gate verdict or relax the thresholds — it is a qualifier on
interpretation, not a license to lower the bar.

---

## Disposition

| | |
|---|---|
| Verdict | **READ (OPTIMISTIC)** |
| Standalone deployable | NO — is_ready() returns False |
| A3 ensemble role | YES — contributes 0.3 × master_trader signal weight |
| Archive required | NO — READ verdict stays active for A3 ensemble |
| Re-test trigger | Only if OOS window grows by ≥100 new trades (new data, not re-tuning) |

A2 earns `is_ready() → True` ONLY after:
1. Additional OOS data accumulates (separate from this IS/OOS window)
2. A fresh gate run on the extended OOS passes all 11 checks including DSR
3. Owner approves deployment per the standing rules

---

## Amendment Log

- 2026-06-12: Initial gate run. Verdict READ. 10/11 pass; DSR fails at z=−25.32.
  Actual run via `scripts/run_a2_gate.py` — see commit for exact code state.
