# Validation Gate Specification v1.0

## Purpose
The Validation Gate is the single source of truth that decides whether any SMC strategy is allowed to move from backtest → paper trading → live trading.

## Gate Decision Matrix (Minimum Requirements)

| Metric                  | Threshold     | Notes                              |
|-------------------------|---------------|------------------------------------|
| Sharpe Ratio            | ≥ 1.8         | Annualized                         |
| Maximum Drawdown        | ≤ 12%         | Peak-to-trough                     |
| Profit Factor           | ≥ 1.6         | Gross profit / Gross loss          |
| Minimum Trades          | 200           | Across multiple instruments        |
| Win Rate                | ≥ 48%         | With positive expectancy           |
| Expectancy              | > 0           | Average $ per trade                |
| Calmar Ratio            | ≥ 1.5         | Annual return / Max DD             |
| Recovery Factor         | ≥ 3.0         | Net profit / Max DD                |

## Required Stress Tests
1. Walk-forward optimization (minimum 4 folds)
2. Purged K-fold cross validation
3. Regime shift test (trending → ranging → volatile)
4. Slippage & spread shock test (+50% spread, 2x slippage)
5. Black swan scenario (NFP, rate decision, flash crash replay)

## Gate Process Flow
1. Strategy submitted via `smc-filter-builder` skill
2. `strategy-validator` skill runs full backtest suite
3. `risk-auditor` skill reviews risk parameters
4. Gate decision logged in `VALIDATION_STATUS.md`
5. Only GREEN status allows paper trading

## Current Status (2026-06-12)
All alphas: **PENDING**

Future versions will include live data replay and real brokerage cost models.

---
## RECONCILIATION NOTE (added 2026-06-12)
These thresholds differ from the locked GATE_DECISION.md thresholds (Sharpe > 1.2,
Max DD < 15%, PF > 1.25). GATE_DECISION.md is the immutable locked spec — A2 was
gated against those thresholds. This document is a planning reference only.
Any threshold change for future alphas requires a new lock-before-look commit
before data exposure.
