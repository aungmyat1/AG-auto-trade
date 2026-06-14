"""Run the Trading Readiness Gate System (TRGS) and emit a readiness report.

    python3 scripts/run_readiness_gate.py [--out readiness_report.json]

With no real gate verdict / execution layer, the honest answer today is BLOCKED:
the replay validator catches the live LF-1 liquidity look-ahead, there is no
ROBUST verdict, and the execution layer does not exist. That is the firewall
working — it must say NO until the system has earned a YES.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from ag.alpha.a1_smc_momentum.detectors.bos_choch import BosChochDetector
from ag.alpha.a1_smc_momentum.detectors.displacement import DisplacementDetector
from ag.alpha.a1_smc_momentum.detectors.fvg import FairValueGapDetector
from ag.alpha.a1_smc_momentum.detectors.liquidity import LiquidityDetector
from ag.alpha.a1_smc_momentum.detectors.order_block import OrderBlockDetector
from ag.readiness import evaluate_readiness


def _synthetic_ohlcv(n: int = 300, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    o_l, h_l, l_l, c_l, v_l = [], [], [], [], []
    price = 1800.0
    for i in range(n):
        drift = 0.8 if (i // 25) % 2 == 0 else -0.8
        o = price
        c = price + rng.normal(drift, 2.0)
        hi = max(o, c) + abs(rng.normal(0, 1.0))
        lo = min(o, c) - abs(rng.normal(0, 1.0))
        if i in (88, 89, 90):
            c, hi, lo = o + 16.0, o + 16.6, o + 0.4
        o_l.append(o)
        h_l.append(hi)
        l_l.append(lo)
        c_l.append(c)
        v_l.append(float(rng.integers(1000, 5000)))
        price = c
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(
        {"open": o_l, "high": h_l, "low": l_l, "close": c_l, "volume": v_l}, index=idx
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Trading Readiness Gate (TRGS)")
    ap.add_argument("--out", default="readiness_report.json")
    ap.add_argument("--override", action="store_true",
                    help="owner manual override (does NOT enable live; LIVE_TRADING is separate)")
    args = ap.parse_args()

    detect_fns = [
        ("order_block", OrderBlockDetector(displacement_atr_mult=0.5, atr_window=5, lookback=3).detect),
        ("fvg", FairValueGapDetector(min_size_atr=0.2, atr_window=5).detect),
        ("liquidity", LiquidityDetector(swing_lookback=3, cluster_atr_mult=0.3, atr_window=5).detect),
        ("bos_choch", BosChochDetector(swing_lookback=3, atr_window=5).detect),
        ("displacement", DisplacementDetector(atr_mult=0.8, atr_window=5).detect),
    ]

    report = evaluate_readiness(
        detect_fns=detect_fns,
        df=_synthetic_ohlcv(),
        gate_result=None,          # no ROBUST verdict exists yet
        manual_override=args.override,
    )

    print(report.summary())
    pathlib.Path(args.out).write_text(report.to_json())
    print(f"\nWrote {args.out}")
    # Non-zero exit when not cleared for live — usable as a CI / deploy gate.
    sys.exit(0 if report.can_trade_live else 1)


if __name__ == "__main__":
    main()
