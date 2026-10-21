"""Unit tests for the shared mean-gap arithmetic (`domain/cadence_math.py`).

This function is the single home for "how often does this move?" after D3 in
`IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` collapsed three copies of it
(pantry belief, buy verdict, stocktake cadence auto-tuner). It's tiny, pure,
and load-bearing for all three, so it's worth pinning directly — the
alternative is re-deriving the same edge cases from three callers' tests.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from dora_api.domain.cadence_math import mean_gap_days


def test__no_points__is_none():
    assert mean_gap_days([]) is None


def test__single_point__is_none():
    assert mean_gap_days([date(2026, 8, 1)]) is None


def test__two_dates__is_the_gap():
    assert mean_gap_days([date(2026, 8, 1), date(2026, 8, 15)]) == 14.0


def test__evenly_spaced_dates__is_the_spacing():
    dates = [date(2026, 1, 1) + timedelta(days=7 * i) for i in range(5)]
    assert mean_gap_days(dates) == 7.0


def test__unsorted_input__is_sorted_first():
    """Callers pass purchase dates, change timestamps, and set-derived
    collections; requiring pre-sorting would be a trap."""
    ordered = [date(2026, 3, 1), date(2026, 3, 11), date(2026, 3, 21)]
    assert mean_gap_days(list(reversed(ordered))) == mean_gap_days(ordered) == 10.0


def test__duplicate_dates__are_not_zero_day_gaps():
    """Two purchases logged on the same day is one shopping trip, not a
    zero-day cadence. Dropping the pair keeps the real 10-day gap; counting
    it would halve the average and read as a much faster-moving item."""
    dates = [date(2026, 5, 1), date(2026, 5, 1), date(2026, 5, 11)]
    assert mean_gap_days(dates) == 10.0


def test__all_points_identical__is_none_not_zero():
    """`None` means "no signal, keep your fallback". A 0.0 here would make
    the cadence auto-tuner read a double-entry as the fastest band."""
    d = date(2026, 5, 1)
    assert mean_gap_days([d, d, d]) is None


def test__datetimes_keep_sub_day_precision():
    """The stocktake auto-tuner averages StockLevelChange timestamps, where
    a same-day pair is a real (short) gap rather than a duplicate."""
    base = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    gap = mean_gap_days([base, base + timedelta(hours=12)])
    assert gap == pytest.approx(0.5)


def test__mean_is_over_gaps_not_points():
    """3 points → 2 gaps (4 and 10 days) → mean 7, not a span/count mix-up."""
    dates = [date(2026, 7, 1), date(2026, 7, 5), date(2026, 7, 15)]
    assert mean_gap_days(dates) == 7.0
