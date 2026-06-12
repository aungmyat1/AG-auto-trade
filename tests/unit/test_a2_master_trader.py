"""
Unit tests for A2 master-trader copy module.

Coverage:
- loader: split_is_oos boundary conditions
- replay: reference_pip, r_multiples, cost_model
- a2: A2MasterTrader.propose() signal routing and is_ready()
"""
from __future__ import annotations

import pytest

from ag.alpha.a2_master_trader.loader import RawTrade, SplitResult, split_is_oos, IS_N
from ag.alpha.a2_master_trader.replay import (
    compute_reference_pip,
    trades_to_r_multiples,
    make_cost_model,
    COPY_LAG_PIPS,
    PIP_SIZE_USD,
)
from ag.alpha.a2_master_trader.a2 import A2MasterTrader, COPY_LAG_SECONDS


# ── Helpers ──────────────────────────────────────────────────────────────────

def _trade(entry: float, exit_: float, side: str = "BUY",
           open_dt: str = "2025-01-01T00:00:00+00:00",
           close_dt: str = "2025-01-01T01:00:00+00:00",
           hold_hours: float = 1.0) -> RawTrade:
    return RawTrade(
        entry_price=entry,
        exit_price=exit_,
        side=side,
        open_time_dt=open_dt,
        close_time_dt=close_dt,
        hold_hours=hold_hours,
    )


def _make_trades(n: int, entry: float = 2000.0, exit_: float = 2001.5, side: str = "BUY") -> list[RawTrade]:
    return [_trade(entry, exit_, side) for _ in range(n)]


# ── loader ────────────────────────────────────────────────────────────────────

class TestSplitIsOos:
    def test_basic_split(self):
        trades = _make_trades(300)
        split = split_is_oos(trades)
        assert len(split.is_trades) == IS_N
        assert len(split.oos_trades) == 300 - IS_N
        assert split.total_n == 300

    def test_split_preserves_order(self):
        trades = _make_trades(250)
        split = split_is_oos(trades)
        assert split.is_trades[-1] is trades[IS_N - 1]
        assert split.oos_trades[0] is trades[IS_N]

    def test_cutoff_dt_matches_last_is_trade(self):
        trades = [_trade(2000, 2001, open_dt=f"2025-0{i+1}-01T00:00:00+00:00") for i in range(250)]
        split = split_is_oos(trades)
        assert split.is_cutoff_dt == trades[IS_N - 1].open_time_dt

    def test_raises_on_insufficient_trades(self):
        with pytest.raises(ValueError, match="Insufficient"):
            split_is_oos(_make_trades(IS_N))  # exactly IS_N = no OOS

    def test_custom_is_n(self):
        trades = _make_trades(120)
        split = split_is_oos(trades, is_n=50)
        assert len(split.is_trades) == 50
        assert len(split.oos_trades) == 70


# ── replay ────────────────────────────────────────────────────────────────────

class TestComputeReferencePip:
    def test_median_absolute_move(self):
        trades = [
            _trade(2000.0, 2001.0),  # |move| = 1.0
            _trade(2000.0, 2003.0),  # |move| = 3.0
            _trade(2000.0, 1998.0),  # |move| = 2.0
        ]
        ref = compute_reference_pip(trades)
        assert ref == pytest.approx(2.0)

    def test_single_trade(self):
        trades = [_trade(2000.0, 2001.5)]
        assert compute_reference_pip(trades) == pytest.approx(1.5)

    def test_raises_on_empty(self):
        with pytest.raises(ValueError, match="empty"):
            compute_reference_pip([])


class TestTradesToRMultiples:
    def test_buy_win(self):
        trades = [_trade(2000.0, 2001.3, "BUY")]
        r = trades_to_r_multiples(trades, reference_pip=1.3)
        assert r[0] == pytest.approx(1.0)

    def test_sell_win(self):
        # SELL: price goes down → profit
        trades = [_trade(2000.0, 1998.7, "SELL")]
        r = trades_to_r_multiples(trades, reference_pip=1.3)
        assert r[0] == pytest.approx(1.0)

    def test_buy_loss(self):
        trades = [_trade(2000.0, 1998.7, "BUY")]
        r = trades_to_r_multiples(trades, reference_pip=1.3)
        assert r[0] == pytest.approx(-1.0)

    def test_raises_on_nonpositive_ref_pip(self):
        with pytest.raises(ValueError, match="positive"):
            trades_to_r_multiples([_trade(2000, 2001)], reference_pip=0.0)

    def test_multiple_trades_preserves_order(self):
        trades = [_trade(2000.0, 2002.6, "BUY"), _trade(2000.0, 1997.4, "SELL")]
        r = trades_to_r_multiples(trades, reference_pip=1.3)
        assert r[0] == pytest.approx(2.0)
        assert r[1] == pytest.approx(2.0)


class TestMakeCostModel:
    def test_total_r_correct(self):
        ref_pip = 1.305
        cm = make_cost_model(ref_pip)
        expected_total = (COPY_LAG_PIPS * PIP_SIZE_USD) / ref_pip
        assert cm.total_r == pytest.approx(expected_total, rel=1e-4)

    def test_components_sum_to_total(self):
        cm = make_cost_model(1.305)
        assert cm.spread_r + cm.commission_r + cm.slippage_r == pytest.approx(cm.total_r, rel=1e-9)

    def test_total_r_scales_with_ref_pip(self):
        # Larger reference pip → smaller cost in R
        cm_narrow = make_cost_model(0.5)
        cm_wide = make_cost_model(2.0)
        assert cm_narrow.total_r > cm_wide.total_r


# ── A2MasterTrader ────────────────────────────────────────────────────────────

def _open_trade_dict(
    open_ts_ms: int,
    close_ts_ms: int,
    side: str = "BUY",
    entry_price: float = 2000.0,
    exit_price: float = 2002.0,
) -> dict:
    return {
        "open_time_ms": open_ts_ms,
        "close_time_ms": close_ts_ms,
        "side": side,
        "entry_price": entry_price,
        "exit_price": exit_price,
    }


class TestA2MasterTrader:
    BASE_TS = 1_700_000_000_000  # arbitrary ms epoch

    def test_is_ready_false_by_design(self):
        a2 = A2MasterTrader()
        assert a2.is_ready() is False

    def test_no_signal_with_no_trades(self):
        a2 = A2MasterTrader(open_trades=[])
        signal = a2.propose({"timestamp_ms": self.BASE_TS, "price": 2000.0})
        assert signal is None

    def test_signal_during_open_trade(self):
        lag_ms = COPY_LAG_SECONDS * 1000
        open_ts = self.BASE_TS
        close_ts = self.BASE_TS + 3_600_000  # 1 hour later
        context_ts = open_ts + lag_ms + 1_000   # 1 second after copy lag ends

        trade = _open_trade_dict(open_ts, close_ts, side="BUY")
        a2 = A2MasterTrader(open_trades=[trade])
        signal = a2.propose({"timestamp_ms": context_ts, "price": 2000.0})

        assert signal is not None
        assert signal.direction == "long"
        assert signal.alpha_id == "A2"

    def test_sell_trade_maps_to_short(self):
        lag_ms = COPY_LAG_SECONDS * 1000
        open_ts = self.BASE_TS
        close_ts = self.BASE_TS + 3_600_000
        context_ts = open_ts + lag_ms + 1_000

        trade = _open_trade_dict(open_ts, close_ts, side="SELL")
        a2 = A2MasterTrader(open_trades=[trade])
        signal = a2.propose({"timestamp_ms": context_ts, "price": 2000.0})

        assert signal is not None
        assert signal.direction == "short"

    def test_no_signal_before_copy_lag_expires(self):
        lag_ms = COPY_LAG_SECONDS * 1000
        open_ts = self.BASE_TS
        close_ts = self.BASE_TS + 3_600_000
        context_ts = open_ts + lag_ms - 1_000  # 1 second BEFORE lag expires

        trade = _open_trade_dict(open_ts, close_ts)
        a2 = A2MasterTrader(open_trades=[trade])
        signal = a2.propose({"timestamp_ms": context_ts, "price": 2000.0})
        assert signal is None

    def test_no_signal_after_trade_closes(self):
        lag_ms = COPY_LAG_SECONDS * 1000
        open_ts = self.BASE_TS
        close_ts = self.BASE_TS + 3_600_000
        context_ts = close_ts + 1_000  # 1 second AFTER close

        trade = _open_trade_dict(open_ts, close_ts)
        a2 = A2MasterTrader(open_trades=[trade])
        signal = a2.propose({"timestamp_ms": context_ts, "price": 2000.0})
        assert signal is None

    def test_first_open_trade_wins_on_overlap(self):
        lag_ms = COPY_LAG_SECONDS * 1000
        open_ts = self.BASE_TS
        close_ts = self.BASE_TS + 3_600_000
        context_ts = open_ts + lag_ms + 1_000

        buy_trade = _open_trade_dict(open_ts, close_ts, side="BUY")
        sell_trade = _open_trade_dict(open_ts, close_ts, side="SELL")
        a2 = A2MasterTrader(open_trades=[buy_trade, sell_trade])
        signal = a2.propose({"timestamp_ms": context_ts, "price": 2000.0})
        assert signal.direction == "long"  # first trade wins

    def test_alpha_id_is_A2(self):
        assert A2MasterTrader.alpha_id == "A2"
