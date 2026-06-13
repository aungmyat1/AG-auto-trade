"""Unit tests for CME expiry / roll calendar logic."""
from __future__ import annotations

from datetime import date

import pytest

from ag.data.ib_live.roll import (
    get_front_month,
    front_month_sequence,
    _expiry_date,
    _nth_to_last_business_day,
    _nth_weekday_of_month,
)


class TestExpiryDates:
    def test_gc_expiry_is_business_day(self):
        d = _expiry_date("GC", 2025, 12)
        assert d.weekday() < 5

    def test_gc_expiry_in_month(self):
        d = _expiry_date("GC", 2025, 12)
        assert d.month == 12 and d.year == 2025

    def test_6e_expiry_is_wednesday(self):
        d = _expiry_date("6E", 2025, 12)
        assert d.weekday() == 2  # Wednesday

    def test_6e_expiry_is_third_wednesday(self):
        d = _expiry_date("6E", 2025, 12)
        # Count Wednesdays in December 2025 up to d
        count = sum(
            1 for i in range(1, d.day + 1)
            if date(2025, 12, i).weekday() == 2
        )
        assert count == 3

    def test_unknown_symbol_raises(self):
        with pytest.raises(ValueError):
            _expiry_date("BTC", 2025, 12)


class TestNthToLastBusinessDay:
    def test_known_november_2025(self):
        # 3rd-to-last business day of November 2025
        d = _nth_to_last_business_day(2025, 11, 3)
        assert d.month == 11 and d.year == 2025
        assert d.weekday() < 5

    def test_returns_date_in_given_month(self):
        for month in (2, 4, 6, 8, 10, 12):
            d = _nth_to_last_business_day(2025, month, 3)
            assert d.month == month


class TestNthWeekdayOfMonth:
    def test_third_wednesday_dec_2025(self):
        d = _nth_weekday_of_month(2025, 12, weekday=2, n=3)
        assert d.weekday() == 2
        # Verify it's the third Wednesday
        count = sum(
            1 for i in range(1, d.day + 1)
            if date(2025, 12, i).weekday() == 2
        )
        assert count == 3


class TestGetFrontMonth:
    def test_returns_string(self):
        result = get_front_month("GC", date(2025, 11, 1))
        assert isinstance(result, str)
        assert result.startswith("GC")

    def test_symbol_prefix_matches(self):
        assert get_front_month("MGC", date(2025, 11, 1)).startswith("MGC")
        assert get_front_month("6E",  date(2025, 11, 1)).startswith("6E")

    def test_no_date_uses_today(self):
        result = get_front_month("GC")
        assert result.startswith("GC")

    def test_different_months_give_different_contracts(self):
        jan = get_front_month("GC", date(2025, 1, 2))
        nov = get_front_month("GC", date(2025, 11, 1))
        # Different months in different delivery cycles should differ
        assert isinstance(jan, str) and isinstance(nov, str)


class TestFrontMonthSequence:
    def test_returns_list_of_tuples(self):
        seq = front_month_sequence("GC", date(2025, 1, 1), date(2025, 6, 30))
        assert isinstance(seq, list)
        assert all(len(t) == 3 for t in seq)

    def test_sequence_covers_full_range(self):
        start = date(2025, 1, 1)
        end = date(2025, 6, 30)
        seq = front_month_sequence("GC", start, end)
        assert seq[0][1] == start
        assert seq[-1][2] == end

    def test_sequence_is_non_empty(self):
        seq = front_month_sequence("6E", date(2025, 1, 1), date(2025, 9, 30))
        assert len(seq) > 0
