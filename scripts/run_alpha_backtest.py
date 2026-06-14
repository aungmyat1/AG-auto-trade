"""
Alpha backtest harness — replay OHLCV history through an alpha + RiskEngine.

Routes every bar through alpha.propose() then RiskEngine.validate_entry() and
accumulates a trade CSV suitable for scripts/run_gate.py.

Usage:
    python3 scripts/run_alpha_backtest.py \\
        --alpha a0_mvp \\
        --data data/gc_h1_2022_2024.parquet \\
        --instrument GC \\
        --cost-preset gc \\
        --out results/a0_mvp_trades.csv

Then gate it:
    python3 scripts/run_gate.py results/a0_mvp_trades.csv \\
        --instrument GC --cost-preset gc --n-trials 1

Supported alphas (--alpha):
    a0_mvp      A0_MVP: sweep+choch only (PipelineConfig(sweep=True, choch=True))
    a1          A1SmcMomentum (full config)
    a2          A2MasterTrader (requires --master-data path)

Note: Data loading (Databento parquet) is blocked until Phase B (Databento subscription).
      Run with --synthetic to use auto-generated OHLCV for smoke-testing.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys
from typing import List, Optional

# ── ensure repo root is on sys.path when run as a script ───────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from ag.alpha.base import AlphaModule, SignalProposal
from ag.risk.engine import RiskEngine, RiskConfig
from ag.validation.cost_model import CostModel


def _build_alpha(alpha_name: str, master_data: Optional[str] = None) -> AlphaModule:
    """Instantiate the requested alpha module."""
    if alpha_name == "a0_mvp":
        from ag.alpha.a1_smc_momentum.a1_alpha import A1SmcMomentum
        from ag.alpha.a1_smc_momentum.pipeline import PipelineConfig
        alpha = A1SmcMomentum(config=PipelineConfig(sweep=True, choch=True,
                                                     ob=False, fvg=False,
                                                     displacement=False))
        alpha.alpha_id = "A0_MVP"
        return alpha

    if alpha_name == "a1":
        from ag.alpha.a1_smc_momentum.a1_alpha import A1SmcMomentum
        return A1SmcMomentum()

    if alpha_name == "a2":
        from ag.alpha.a2_master_trader.a2 import A2MasterTrader
        if master_data is None:
            raise ValueError("--master-data required for a2")
        return A2MasterTrader(master_data_path=master_data)

    raise ValueError(f"Unknown alpha: {alpha_name!r}. Choose: a0_mvp, a1, a2")


def _make_synthetic_df(n_bars: int = 500):
    """Generate synthetic OHLCV for smoke-testing when no real data available."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        return None

    rng = np.random.default_rng(42)
    close = 1800.0 + np.cumsum(rng.normal(0, 2, n_bars))
    high = close + rng.uniform(0.5, 3, n_bars)
    low = close - rng.uniform(0.5, 3, n_bars)
    open_ = close + rng.normal(0, 1, n_bars)
    volume = rng.integers(1000, 5000, n_bars).astype(float)
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                         "close": close, "volume": volume})


def _load_parquet(path: str):
    try:
        import pandas as pd
        return pd.read_parquet(path)
    except Exception as exc:
        print(f"ERROR loading {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def run_backtest(
    alpha: AlphaModule,
    df,
    risk_engine: RiskEngine,
    lookback: int = 50,
) -> List[dict]:
    """
    Replay bars through alpha + risk engine.

    Returns list of trade dicts with fields:
        bar_idx, direction, entry_price, stop_pct, target_pct,
        r_multiple, approved, rejection_reason
    """
    trades = []
    n = len(df)

    for i in range(lookback, n):
        window = df.iloc[i - lookback: i + 1]
        market_data = {"df": window}

        proposal: Optional[SignalProposal] = alpha.propose(market_data)
        if proposal is None:
            continue

        # Route through risk engine (required on every entry path)
        decision = risk_engine.validate_entry(
            position_size_pct=0.005,
            leverage=1.0,
        )

        entry_price = float(df["close"].iloc[i])
        stop_dist = proposal.stop_distance_pct / 100.0
        target_dist = proposal.target_distance_pct / 100.0

        trade = {
            "bar_idx": i,
            "direction": proposal.direction,
            "entry_price": entry_price,
            "stop_pct": stop_dist,
            "target_pct": target_dist,
            "confidence": round(proposal.confidence, 4),
            "rationale": proposal.entry_rationale,
            "risk_approved": decision.approved,
            "risk_violations": "|".join(decision.violations),
        }

        if decision.approved:
            # Simple simulation: compute R-multiple based on next bar close
            if i + 1 < n:
                next_close = float(df["close"].iloc[i + 1])
                pct_move = (next_close - entry_price) / entry_price
                if proposal.direction == "short":
                    pct_move = -pct_move
                # R-multiple: how many R units did this trade return?
                r = pct_move / stop_dist
                trade["r_multiple"] = round(r, 4)
                risk_engine.open_position(f"t{i}")
                risk_engine.record_trade_result(pct_move * 0.005, f"t{i}")
            else:
                trade["r_multiple"] = 0.0
        else:
            trade["r_multiple"] = 0.0

        trades.append(trade)

    return trades


def _write_gate_csv(approved_trades: List[dict], out_path: pathlib.Path) -> None:
    """Write gate-ready CSV: only risk-approved trades, column named pnl_r."""
    if not approved_trades:
        print("No approved trades to write.", file=sys.stderr)
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["pnl_r"])
        writer.writeheader()
        for t in approved_trades:
            writer.writerow({"pnl_r": t["r_multiple"]})
    print(f"Wrote {len(approved_trades)} approved trades → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Alpha backtest harness")
    parser.add_argument("--alpha", required=True, choices=["a0_mvp", "a1", "a2"])
    parser.add_argument("--data", help="Path to OHLCV parquet file")
    parser.add_argument("--instrument", default="GC", choices=["GC", "MGC", "6E"])
    parser.add_argument("--cost-preset", default="gc", choices=["gc", "6e"])
    parser.add_argument("--master-data", help="Path to master trader CSV (a2 only)")
    parser.add_argument("--out", default="results/trades.csv")
    parser.add_argument("--lookback", type=int, default=50)
    parser.add_argument("--synthetic", action="store_true",
                        help="Use synthetic OHLCV (smoke-test; no Databento needed)")
    args = parser.parse_args()

    # Load data
    if args.synthetic:
        print("Using synthetic OHLCV (500 bars)...")
        df = _make_synthetic_df(500)
        if df is None:
            print("ERROR: pandas/numpy required for synthetic mode.", file=sys.stderr)
            sys.exit(1)
    elif args.data:
        df = _load_parquet(args.data)
    else:
        parser.error("Provide --data <path> or --synthetic")

    print(f"Loaded {len(df)} bars.")

    # Build alpha
    alpha = _build_alpha(args.alpha, args.master_data)
    risk_engine = RiskEngine(RiskConfig())
    # cost_model applied by run_gate.py on the CSV output (net-of-cost scoring happens there)
    _cost_model = CostModel.for_gc() if args.cost_preset == "gc" else CostModel.for_6e()

    print(f"Running backtest: alpha={alpha.alpha_id}, instrument={args.instrument}, "
          f"cost_preset={args.cost_preset}")
    trades = run_backtest(alpha, df, risk_engine, lookback=args.lookback)

    approved = [t for t in trades if t["risk_approved"]]
    print(f"Signals: {len(trades)} | Risk-approved: {len(approved)}")

    if approved:
        r_multiples = [t["r_multiple"] for t in approved]
        wins = sum(1 for r in r_multiples if r > 0)
        print(f"Win rate: {wins/len(r_multiples):.1%} | "
              f"Mean R: {sum(r_multiples)/len(r_multiples):.3f}")

    # Write gate-ready CSV (approved trades only, pnl_r column)
    _write_gate_csv(approved, pathlib.Path(args.out))

    if len(approved) < 50:
        print(
            f"\nWARNING: only {len(approved)} approved trades — below READ floor (n=50).\n"
            "Do not run the gate. Investigate signal rate first.",
            file=sys.stderr,
        )
    else:
        print(f"\nNext step: python3 scripts/run_gate.py {args.out} "
              f"--instrument {args.instrument} --cost-preset {args.cost_preset} "
              f"--n-trials <count from trial_log>")


if __name__ == "__main__":
    main()
