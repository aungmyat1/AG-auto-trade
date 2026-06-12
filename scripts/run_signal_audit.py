#!/usr/bin/env python3
"""Signal pipeline audit — progressive filter analysis.

Addresses the "1 trade per 363 pair-days" failure mode: this script
instruments every stage of the SMC signal pipeline and shows exactly
where setups are being filtered out.

Usage:
    python scripts/run_signal_audit.py                     # default 500 bars, trending
    python scripts/run_signal_audit.py --n-bars 1000 --scenario choppy

Output for each filter config:
    === 1. sweep+choch (MVP) ===
    === Signal Funnel Report ===
      Bars processed:           500
      Liquidity sweeps:          24
      BOS events:                18
      CHOCH events:               6
      ...
    Bottleneck: sweeps → choch

Interpretation:
  - If "Liquidity sweeps: 2" → your swing_lookback is too strict; lower it.
  - If "sweeps → choch" is the bottleneck → CHOCH fires rarely; widen lookback.
  - If "choch → where_active: 0" → WHERE filters kill everything after CHOCH.
  - "Entries generated: 0" when sweeps AND choch > 0 → entry logic bug.

The script does NOT generate trades — it is pure signal measurement (read-only).
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

# Allow running from repo root: python scripts/run_signal_audit.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig, SmcPipeline
from ag.validation.signal_audit import SignalFunnelTracker


# ── Synthetic data generators ─────────────────────────────────────────────────

def _trending_ohlcv(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Uptrend → pullback → downtrend.  Creates sweeps, BOS, CHOCH events."""
    rng = random.Random(seed)
    price = 100.0
    rows = []
    for i in range(n):
        # Trend direction reverses halfway
        drift = 0.025 if i < n // 2 else -0.015
        body = rng.gauss(drift, 0.35)
        wick_up = abs(rng.gauss(0, 0.18))
        wick_dn = abs(rng.gauss(0, 0.18))
        o = price
        c = price + body
        h = max(o, c) + wick_up
        lo = min(o, c) - wick_dn
        rows.append({"open": o, "high": h, "low": lo, "close": c,
                     "volume": rng.randint(500, 5000)})
        price = c
    return pd.DataFrame(rows)


def _choppy_ohlcv(n: int = 500, seed: int = 99) -> pd.DataFrame:
    """Bounded range with no clear trend.  Fewer structure events."""
    rng = random.Random(seed)
    price = 100.0
    rows = []
    for i in range(n):
        body = rng.gauss(0.0, 0.45)
        wick_up = abs(rng.gauss(0, 0.22))
        wick_dn = abs(rng.gauss(0, 0.22))
        o = price
        c = max(92.0, min(108.0, price + body))
        h = max(o, c) + wick_up
        lo = min(o, c) - wick_dn
        rows.append({"open": o, "high": h, "low": lo, "close": c,
                     "volume": rng.randint(200, 2000)})
        price = c
    return pd.DataFrame(rows)


# ── Audit runner ──────────────────────────────────────────────────────────────

def run_config(
    df: pd.DataFrame,
    config: PipelineConfig,
    label: str,
) -> SignalFunnelTracker:
    tracker = SignalFunnelTracker()
    SmcPipeline(config).run(df, audit_tracker=tracker)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)
    print(tracker.report())
    bottleneck = tracker.bottleneck()
    print(f"\n  ▶  Bottleneck: {bottleneck}")
    return tracker


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SMC signal pipeline audit — find where trades disappear."
    )
    parser.add_argument("--n-bars", type=int, default=500,
                        help="Number of OHLCV bars to simulate (default 500)")
    parser.add_argument("--scenario", choices=["trending", "choppy"], default="trending",
                        help="Market scenario (default: trending)")
    parser.add_argument("--lookback", type=int, default=3,
                        help="swing_lookback for detectors (default 3; lower = more signals)")
    parser.add_argument("--atr-window", type=int, default=10,
                        help="ATR window (default 10)")
    args = parser.parse_args()

    if args.scenario == "trending":
        df = _trending_ohlcv(args.n_bars)
    else:
        df = _choppy_ohlcv(args.n_bars)

    n = args.lookback
    w = args.atr_window

    print("\nSignal Pipeline Audit")
    print(f"Scenario: {args.scenario} | Bars: {len(df)} | "
          f"swing_lookback={n} | atr_window={w}")
    print("\nRule: add one filter at a time.  Each filter must ADD positive")
    print("expectancy WITHOUT destroying trade count before the next is added.")

    trackers = []

    # Step 1 — MVP: sweep + CHOCH only (start here, nothing else)
    trackers.append(run_config(
        df,
        PipelineConfig(sweep=True, choch=True, ob=False, fvg=False,
                       displacement=False, swing_lookback=n, atr_window=w),
        "1. sweep+choch  ← Phase B MVP: measure this baseline first",
    ))

    # Step 2 — add OB filter
    trackers.append(run_config(
        df,
        PipelineConfig(sweep=True, choch=True, ob=True, fvg=False,
                       displacement=False, swing_lookback=n, atr_window=w),
        "2. sweep+choch+ob  ← adds OB zone requirement",
    ))

    # Step 3 — add FVG
    trackers.append(run_config(
        df,
        PipelineConfig(sweep=True, choch=True, ob=True, fvg=True,
                       displacement=False, swing_lookback=n, atr_window=w),
        "3. sweep+choch+ob+fvg  ← adds FVG confluence",
    ))

    # Step 4 — full config (all 5 detectors)
    trackers.append(run_config(
        df,
        PipelineConfig(sweep=True, choch=True, ob=True, fvg=True,
                       displacement=True, swing_lookback=n, atr_window=w),
        "4. full (all 5 detectors)  ← A+ setup, likely over-filtered",
    ))

    # Summary
    print(f"\n{'='*60}")
    print("  Summary: trade count at each filter level")
    print(f"{'='*60}")
    labels = ["sweep+choch", "sweep+choch+ob", "+fvg", "full (all 5)"]
    for lbl, t in zip(labels, trackers):
        sweeps = t.counts.sweeps_detected
        bos = t.counts.bos_detected
        choch = t.counts.choch_detected
        print(f"  {lbl:<25} sweeps={sweeps:>4}  bos={bos:>4}  choch={choch:>4}")

    print("\nIf the full config has 0–1 setups where sweep+choch has 10+,")
    print("the bottleneck is filter over-stacking — start with MVP, add one filter")
    print("at a time and measure each filter's expectancy contribution separately.")


if __name__ == "__main__":
    main()
