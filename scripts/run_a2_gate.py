#!/usr/bin/env python3
"""
A2 gate runner — end-to-end: load DB → IS/OOS split → R-multiples → ValidationGate.

Usage:
    python scripts/run_a2_gate.py [--db PATH]

Default DB path: data/master_traders/master_traders/master_trader_trades.db

Trial count is locked at floor=11 per:
  ag/validation/lock_before_look/A2_MASTER_TRADER_DECISION.md §4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ag.alpha.a2_master_trader.loader import (
    load_master_trades,
    split_is_oos,
    SELECTED_UID,
    IS_N,
)
from ag.alpha.a2_master_trader.replay import (
    compute_reference_pip,
    trades_to_r_multiples,
    make_cost_model,
)
from ag.validation.gate import ValidationGate
from ag.validation.metrics import BacktestResult

DEFAULT_DB = Path(__file__).parent.parent / "data/master_traders/master_traders/master_trader_trades.db"
N_TRIALS = 11  # locked floor; do NOT change without incrementing in the decision doc


def run(db_path: Path) -> None:
    print(f"A2 Gate Runner — trader {SELECTED_UID}, IS_N={IS_N}, n_trials={N_TRIALS}")
    print(f"DB: {db_path}")
    print()

    # 1. Load and split
    trades = load_master_trades(db_path)
    split = split_is_oos(trades)
    print(f"Total trades:  {split.total_n}")
    print(f"IS trades:     {len(split.is_trades)}  (cutoff: {split.is_cutoff_dt})")
    print(f"OOS trades:    {len(split.oos_trades)} (start: {split.oos_start_dt})")
    print()

    # 2. Reference pip from IS
    ref_pip = compute_reference_pip(split.is_trades)
    print(f"Reference pip (IS median |exit-entry|): {ref_pip:.4f} $/oz")

    # 3. OOS R-multiples (gross) + cost model
    oos_r = trades_to_r_multiples(split.oos_trades, ref_pip)
    cost_model = make_cost_model(ref_pip)
    print(f"Cost per trade:  {cost_model.total_r:.4f}R  "
          f"(spread={cost_model.spread_r:.4f} + commission={cost_model.commission_r:.4f} + "
          f"slippage={cost_model.slippage_r:.4f})")
    print()

    # 4. Run gate
    result = BacktestResult(
        trades_r=oos_r,
        instrument="XAUUSD",
        timeframe="copy",
        start_date=split.oos_start_dt,
        end_date=split.oos_trades[-1].close_time_dt,
    )
    gate = ValidationGate()
    gate_result = gate.run(result, cost_model, n_trials=N_TRIALS)

    print(gate_result.report())
    print()

    # 5. Summary
    failed = gate_result.failed_checks
    if failed:
        print(f"Failed checks ({len(failed)}/{len(gate_result.checks)}): {', '.join(failed)}")
    else:
        print("All checks passed.")

    print("\nSURVIVORSHIP NOTE: verdict is OPTIMISTIC (recently-delisted visible; "
          "historically-delisted absent). See A2_MASTER_TRADER_DECISION.md §0.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run A2 validation gate")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to master_trader_trades.db")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        sys.exit(1)

    run(args.db)


if __name__ == "__main__":
    main()
