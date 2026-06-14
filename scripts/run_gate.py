"""
CLI: run the ValidationGate battery on a CSV of trades.

Usage:
    python scripts/run_gate.py trades.csv --instrument GC --n-trials 15

CSV format: one column named 'pnl_r' with per-trade R-multiples, chronological.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ag.validation import ValidationGate, BacktestResult, CostModel


def load_trades(path: str) -> list[float]:
    trades = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(float(row["pnl_r"]))
    return trades


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AG validation gate battery")
    parser.add_argument("csv", help="Path to trades CSV with 'pnl_r' column")
    parser.add_argument("--instrument", default="", help="Instrument name (GC, MGC, 6E)")
    parser.add_argument("--timeframe", default="", help="Timeframe (e.g. 5m, 1h)")
    parser.add_argument("--n-trials", type=int, default=1,
                        help="Number of parameter combos tried (for DSR inflation)")
    parser.add_argument("--cost-preset", default="default",
                        choices=["default", "gc", "mgc", "6e", "zero"],
                        help="Cost model preset")
    args = parser.parse_args()

    try:
        trades_r = load_trades(args.csv)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print("ERROR: CSV must have a 'pnl_r' column", file=sys.stderr)
        sys.exit(1)

    cost = {
        "default": CostModel(),
        "gc": CostModel.for_gc(),
        "mgc": CostModel.for_mgc(),
        "6e": CostModel.for_6e(),
        "zero": CostModel(0, 0, 0),
    }[args.cost_preset]

    result = BacktestResult(
        trades_r=trades_r,
        instrument=args.instrument,
        timeframe=args.timeframe,
        n_trials=args.n_trials,
    )

    gate = ValidationGate()
    gate_result = gate.run(result, cost, n_trials=args.n_trials)

    print(gate_result.report())
    sys.exit(0 if gate_result.verdict == "ROBUST" else 1)


if __name__ == "__main__":
    main()
