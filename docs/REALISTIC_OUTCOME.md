# AG Auto-Trade — Realistic Outcome Assessment

> Purpose: keep expectations objective and prevent goal drift (validation platform → "profitable
> bot quickly"). Companion to `docs/ROADMAP.md` and `docs/SUCCESS_CRITERIA.md`. Updated 2026-06-14.

## One-line summary

The platform (~90% built) is a **strategy-validation system**. Whether SMC has a robust, tradable
edge on gold futures is **not yet determined** — current evidence does not demonstrate one, and the
gate will confirm or reject it on real data.

---

## Observed facts

- Prior SMC backtests have not passed rigorous validation: SMC H1 (crypto) **FRAGILE**
  (CPCV 0.92, MC 0.89); SMC 5-minute (crypto) **FAIL** (PF 0.08); SMC on EURUSD/XAUUSD H1/H4
  **FAIL** (PF 0.70–0.89).
- The master-trader copy (A2) scored **READ, not ROBUST** — strong raw metrics (PF 3.7,
  Sharpe 6.3) but failed the Deflated-Sharpe multiple-testing check (z = −25).
- No SMC strategy has yet been tested on **GC futures** data (the target instrument).
- Platform: validation gate, 6-guard risk engine, SMC detectors, data layer — **498 tests green**.

## Assumptions

- Realistic CME costs (commission + spread + slippage) materially affect net results — modeled.
- GC behaves differently enough from crypto/spot-FX that prior negatives are **not** dispositive
  for GC; they set a skeptical prior, not a conclusion.
- Multi-year, multi-regime 1m data (Databento) is required for the gate's CPCV/WF to be meaningful.

## Hypotheses (to be tested, not assumed)

- **H1 (A1):** SMC as a *WHERE* filter + a momentum/delta *WHEN* trigger produces a robust,
  net-of-cost edge on GC. **Untested.**
- **H0 (A0_MVP):** sweep+ChoCH→entry is a *plumbing* check only; expected FRAGILE (it is the
  archived SMC_H1 pattern). Confirms the pipeline runs; tests nothing about H1.

## Success criteria

The bar is the **locked, immutable gate** (`GATE_DECISION.md`), not any later-chosen number:
n ≥ 200 net trades · net PF > 1.25 · Sharpe > 1.2 · win rate > 45% · max DD < 15% ·
CPCV median PF > 1.0 · WF pass ≥ 60% · MC 5th-pct PF > 0.9 · DSR z > 0.
Promotion gates beyond the backtest live in `docs/SUCCESS_CRITERIA.md`.

---

## Four possible outcomes (prepare for all)

| Outcome | Result | What it means |
|---------|--------|---------------|
| **A** | Profitable SMC strategy | An alpha clears ROBUST → dry-run → shadow → small live. Best case; treat live edge as thinner than backtest. |
| **B** | Platform succeeds, SMC fails | Gate works; SMC shows no robust edge on GC. The validation engine stands, ready for the next strategy. **Most consistent with the current prior.** |
| **C** | SMC works only in specific regimes | Edge appears in (e.g.) EXPANSION but not CHOP. Regime-gated deployment, smaller scope — needs its own validation. |
| **D** | Hypothesis rejected | SMC does not survive on GC in any regime. A clean, well-evidenced "no" — achieved without risking capital. |

The roadmap and gate are built to handle **all four** — none is a project failure; only deploying
an unvalidated strategy would be.

---

## Assets produced regardless of strategy outcome

Even under outcome B/D, the project still owns reusable infrastructure (status as of 2026-06-14):

| Asset | Status | Note |
|-------|--------|------|
| Verification framework (CPCV·WF·MC·DSR·cost) | ✅ Built | **The core asset** — tests *any* strategy |
| Risk engine (6 non-bypassable guards) | ✅ Built | Instrument-agnostic |
| Data connectors (Databento + IB) | ✅ Built | CME futures — *not* crypto exchange connectors |
| Backtest / replay harness | ✅ Built | Bar-by-bar replay → trades CSV |
| SMC detector library | ✅ Built | Reusable WHERE-filter components |
| Regime classifier | ✅ Built | 4-regime context |
| Monitoring (Telegram) | 🟡 Stub | Expand at deployment |
| Trade journal / state machine | ⬜ Phase D | Built only after a ROBUST verdict |
| Optimization pipeline | ⛔ Deferred | Intentionally *not* pre-gate (validation before optimization) |

## What it will not be (near-term)

A guaranteed profit, a money-printing bot, a multi-exchange crypto platform, or a SaaS business.
Those require a proven edge that does not yet exist.

## The reframe that holds regardless of outcome

The asset is the **validation engine**, not any single strategy. A profitable strategy can stop
working; a validation framework can test hundreds. The most valuable milestone right now is **not**
proving SMC works — it is proving the framework can reliably decide whether *any* strategy works.
Once that is solid, SMC, trend-following, mean-reversion, or future AI-generated strategies all run
through the same infrastructure.
