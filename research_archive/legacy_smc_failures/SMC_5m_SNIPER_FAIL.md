# Research Archive — SMC Sniper 5m (freqtrade) FAIL

**Closed:** 2026-06-11
**Status:** DEAD END — do not restart

## Summary

SMC Sniper v1 and v2 both failed the pre-committed L2 gate on BTCUSD/ETHUSD/SOLUSDT 5m perps
in freqtrade. Pre-committed stopping rule was triggered. Experiment closed.

Do NOT re-run this. The root cause is structural (timeframe/SL mismatch), not a
hyper-parameter problem.

## What was tested

| Version | Fix | TRAIN trades | OOS trades | OOS PF | OOS win% |
|---|---|---|---|---|---|
| v1 | Single-OB `_last_zone_ffill` | 0 | 0 | — | — |
| v2 | Multi-OB `active_ob_mask` + windowed sequence | 3–10 (probe) | 16 | 0.079 | 6.2% |

- TRAIN window: 2025-06-12 → 2026-02-03 (235 days), BTC/ETH/SOL on Bybit USDT perps
- VALID OOS window: 2026-02-03 → 2026-06-11 (128 days)
- Framework: freqtrade 2026.5.1, smartmoneyconcepts 0.0.27
- Environment: `/opt/smc-test/` (Docker, Bybit Bybit perps via ccxt)

## L2 gate results (v2 OOS)

| Gate | Required | Achieved | Pass? |
|---|---|---|---|
| n (trade count) | ≥ 30 | 16 | FAIL |
| Profit Factor | > 1.5 | 0.079 | FAIL |
| R:R | ≥ 3.0 | 1.24 | FAIL |
| Win rate | — | 6.2% | — |

Pre-committed stopping rule: "can reach n≥30 only by crushing swing_len until RR collapses" — confirmed at extreme params (htf=8/ltf=4/win=18): 10 trades, 0 wins in TRAIN.

## Root cause

5m CHoCH entry against a 0.27%-underlying SL (0.8% leveraged, 3x) = normal 5m candle
noise stops out the trade before the structural move can develop.

- Single winner (+1.17%): held 4h12m — the structural move eventually arrived
- 15 losers (−0.87% avg): stopped out in 8–27 minutes — normal candle volatility

Signal generation (multi-OB mask, windowed sweep+ChoCH) worked correctly after v2 fix.
The edge is not there because the stop is too tight for the timeframe, not because the
signal is wrong.

## What v2 fixed (for the record)

v1 tracked only the most recent OB via `_last_zone_ffill`, generating zero signals across
363 pair-days. This was a coding failure, not a strategy verdict. v2 correctly implemented
`active_ob_mask()` (flags close inside ANY unmitigated OB), L1 tests 9/9 PASS, but
the underlying edge did not exist at 5m.

## If SMC on crypto is ever revisited

The structural fix is: H1 entry with SL sized to OB boundary distance (not a fixed %).
The H1 variant (`SMCSniperH1Strategy.py`) was built and sanity-tested; it then proceeded
to PREP-2 and failed there too (see `SMC_H1_FRAGILE.md`). Do not re-run 5m without
addressing the timeframe/SL problem first.

## Artefacts

- Strategy code: `research/smc-freqtrade/strategies/SMCSniperStrategy_v2.py` (this repo)
- L1 tests: `research/smc-freqtrade/tests/test_smc_detectors.py` (this repo)
- Memory: `~/.claude/projects/-home-aungp-auto-trade-system/memory/project_smc_sniper_l2_fail.md`
