"""Canonical "how often does this move?" arithmetic.

One home for the mean-gap calculation every cadence-flavoured feature needs
(R-003). Before this module the same math existed three times:

* ``pantry_belief._mean_gap_days``  — mean gap between unique purchase dates.
* ``get_buy_verdict._cadence_detail`` — *identical inputs, identical math*,
  different prose.
* ``cadence.auto_band_from_history`` — the same idea over StockLevelChange
  timestamps.

They could drift (and the first two could already contradict each other on the
same row), which is what `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` D3/D-11 call
out. The function is deliberately tiny and pure — the interesting decisions
(which events count, which window, what the number *means*) stay with the
caller; only the averaging lives here.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Sequence


def _gap_days(earlier: date | datetime, later: date | datetime) -> float:
    """Gap in days. Datetimes keep sub-day precision (a movement log is
    timestamped); plain dates are whole-day, which is all a purchase date can
    honestly claim. ``datetime`` is a ``date`` subclass — check it first."""
    if isinstance(earlier, datetime) and isinstance(later, datetime):
        return (later - earlier).total_seconds() / 86400.0
    return float((later - earlier).days)


def mean_gap_days(points: Iterable[date | datetime]) -> float | None:
    """Mean *positive* gap, in days, between consecutive points.

    Returns ``None`` when there is no gap to speak of — fewer than two points,
    or every pair landing on the same instant/day. ``None`` means "no signal,
    keep your fallback", never "zero days": a caller that treated same-day
    duplicates as a zero-day cadence would read a double-entry as the
    fastest-moving item in the pantry.

    Input need not be sorted or unique. Mixing ``date`` and ``datetime`` is not
    supported (Python can't order them) — pass one kind.
    """
    ordered: Sequence[date | datetime] = sorted(points)
    gaps = [
        gap for gap in (
            _gap_days(ordered[i - 1], ordered[i])
            for i in range(1, len(ordered))
        )
        if gap > 0
    ]
    if not gaps:
        return None
    return sum(gaps) / len(gaps)


__all__ = ["mean_gap_days"]
