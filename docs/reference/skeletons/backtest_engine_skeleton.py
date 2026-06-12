# REFERENCE SKELETON ONLY — do not import or run
# Source: backtest_engine.py upload 2026-06-12
#
# ISSUES:
#   1. `from ag.risk.position_sizing import PositionSizer` — doesn't exist.
#      RiskEngine (ag/risk/engine.py) already enforces 0.5%/trade (G4 guard).
#   2. `from cost_models.total_cost_calculator import TotalCostCalculator`
#      — wrong path. Use ag.validation.cost_model.CostModel instead.
#   3. Exit logic bug: `signal.take_profit` is referenced after the loop body
#      enters a position, but `signal` on subsequent bars may be None (if
#      generate_signal returns None) causing AttributeError.
#   4. No cost subtraction from PnL — defeats the cost model purpose.
#
# PRODUCTION APPROACH:
#   - Entry R-multiples go into BacktestResult(trades_r=[...])
#   - ValidationGate.run(result, CostModel.for_gc(), n_trials=N)
#   - No separate backtest engine needed for gate validation
#
# WHAT'S USEFUL:
#   - Bar-by-bar iteration pattern (correct approach for walk-forward)
#   - The 50-bar warmup before signals (good; matches swing_lookback needs)

import pandas as pd
from typing import Callable


class BacktestEngine_SKELETON:
    """Reference only. Production uses BacktestResult + ValidationGate."""

    def __init__(self, strategy_fn: Callable, cost_per_trade_r: float = 0.15):
        self.strategy_fn = strategy_fn
        self.cost_per_trade_r = cost_per_trade_r  # use CostModel.total_r in production
        self.trades_r = []  # collect R-multiples for BacktestResult

    def run(self, df: pd.DataFrame, risk_per_trade: float = 0.005) -> dict:
        position = 0
        entry_price = 0.0
        stop_price = 0.0

        for i in range(50, len(df)):  # 50-bar warmup is a good default
            window = df.iloc[: i + 1]
            signal = self.strategy_fn(window)

            if signal and position == 0:
                position = 1 if signal.direction == "long" else -1
                entry_price = signal.entry_price
                stop_price = signal.stop_loss

            elif position != 0:
                close = df["close"].iloc[i]
                # Simple SL/TP exit
                sl_hit = (position == 1 and close <= stop_price) or \
                         (position == -1 and close >= stop_price)
                tp_hit = (position == 1 and close >= signal.take_profit) or \
                         (position == -1 and close <= signal.take_profit)

                if sl_hit or tp_hit:
                    gross_r = (close - entry_price) * position / abs(entry_price - stop_price)
                    net_r = gross_r - self.cost_per_trade_r
                    self.trades_r.append(net_r)
                    position = 0

        return {
            "n_trades": len(self.trades_r),
            "trades_r": self.trades_r,
            # Pass to: BacktestResult(trades_r=self.trades_r)
            # Then:    ValidationGate().run(result, CostModel.for_gc(), n_trials=1)
        }
