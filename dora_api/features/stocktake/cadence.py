"""Stocktake cadence engine — pure logic for the "how often to check"
question (`PROPOSAL_STOCKTAKE_MODE §4`).

The functions here are deliberately pure (dataclass in → dataclass out).
`stocktake.py` gathers the inputs from the repo and delegates the
decision here; the pytest suite drives it directly without DB.

The band system replaces the deprecated per-item `days_until_stocktake_
alert` column as the user-visible cadence dial (§7). That column is not
dropped yet — it's just no longer consulted by the queue.

Bands and rules
---------------
Three bands:

    weekly       →  7 days
    fortnightly  → 14 days   (default)
    monthly      → 30 days

Resolution order for a single item:

1.  Start from `AppSetting.stocktake_default_cadence_band`. That's the
    baseline for everything.
2.  When `AppSetting.stocktake_auto_tuning_enabled`, the movement
    self-tuner overrides the baseline from the item's recent history
    (see `auto_band_from_history`). Items with no history stay on the
    baseline.
3.  If the item hit Low or Out in the last `_LOW_OUT_BUMP_DAYS`, bump
    the resolved band one step faster (Monthly → Fortnightly →
    Weekly). Actively depleting stock should surface sooner.
4.  If the item is Essential (`is_flagged`), bump one more step faster.
    Essential is a coarse per-item lever — the user's design call
    ("nobody would fine-tune per item, but Essential is a useful pre-
    existing toggle").

Capped at Weekly on the fast end.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable


class CadenceBand(str, Enum):
    """Enum wrapper so callers can use CadenceBand.WEEKLY.days rather
    than a bare 7 literal (R-003)."""
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"

    @property
    def days(self) -> int:
        return _BAND_DAYS[self]


_BAND_DAYS: dict[CadenceBand, int] = {
    CadenceBand.WEEKLY: 7,
    CadenceBand.FORTNIGHTLY: 14,
    CadenceBand.MONTHLY: 30,
}

# Order from slowest → fastest, used for the "bump one step faster" op.
_BAND_ORDER: tuple[CadenceBand, ...] = (
    CadenceBand.MONTHLY,
    CadenceBand.FORTNIGHTLY,
    CadenceBand.WEEKLY,
)


DEFAULT_BAND = CadenceBand.FORTNIGHTLY


# ── Auto-tuning thresholds ─────────────────────────────────────────────
# Read from a trailing window of StockLevelChange rows for the item.
# Windows/thresholds live here (R-003 single source) so the queue, the
# tests, and any future assistant tool all resolve to the same number.

_AUTO_HISTORY_WINDOW_DAYS = 90
_AUTO_WEEKLY_THRESHOLD_DAYS = 10   # avg gap ≤ 10 days → Weekly
_AUTO_MONTHLY_THRESHOLD_DAYS = 25  # avg gap ≥ 25 days → Monthly
_LOW_OUT_BUMP_DAYS = 14            # hit Low/Out in this window → bump


def parse_band(raw: str | None) -> CadenceBand:
    """Coerce a stored `AppSetting.stocktake_default_cadence_band`
    string into a `CadenceBand`. Falls back to the module default when
    the stored value is missing / invalid — a bad row should never
    break the queue endpoint."""
    if not raw:
        return DEFAULT_BAND
    try:
        return CadenceBand(raw.strip().lower())
    except ValueError:
        return DEFAULT_BAND


def _bump_faster(band: CadenceBand, steps: int = 1) -> CadenceBand:
    """Move `steps` positions toward Weekly, clamped at Weekly."""
    if steps <= 0:
        return band
    try:
        idx = _BAND_ORDER.index(band)
    except ValueError:
        return band
    return _BAND_ORDER[min(idx + steps, len(_BAND_ORDER) - 1)]


@dataclass(frozen=True, slots=True)
class ItemHistory:
    """Pure inputs for a single item's cadence resolution. The queue
    populates this from the item + its trailing-window
    StockLevelChange rows so the resolver stays DB-free (and testable
    in isolation).
    """
    # When change_timestamps has ≥2 entries, the average gap between
    # consecutive changes over the trailing window (see
    # _AUTO_HISTORY_WINDOW_DAYS) drives Auto. Fewer than 2 → no signal;
    # baseline stands.
    change_timestamps: tuple[datetime, ...]
    # True if any StockLevelChange within the last _LOW_OUT_BUMP_DAYS
    # transitioned the item into Low or Out. Bumps one band faster.
    hit_low_or_out_recently: bool
    # `is_flagged` on the StockItem — bumps one band faster on top of
    # whatever the above produced. §3 of the brief.
    is_essential: bool


def auto_band_from_history(
    change_timestamps: Iterable[datetime],
    now: datetime,
) -> CadenceBand | None:
    """Return the Auto-suggested band from movement history, or `None`
    when there isn't enough history to speak (in which case the caller
    keeps the baseline).

    Uses the trailing `_AUTO_HISTORY_WINDOW_DAYS` window. Needs at
    least 2 changes inside the window to compute an average gap.
    """
    cutoff = now - timedelta(days=_AUTO_HISTORY_WINDOW_DAYS)
    recent = sorted(t for t in change_timestamps if t >= cutoff)
    if len(recent) < 2:
        return None
    gaps = [
        (recent[i] - recent[i - 1]).total_seconds() / 86400.0
        for i in range(1, len(recent))
    ]
    avg_gap = sum(gaps) / len(gaps)
    if avg_gap <= _AUTO_WEEKLY_THRESHOLD_DAYS:
        return CadenceBand.WEEKLY
    if avg_gap >= _AUTO_MONTHLY_THRESHOLD_DAYS:
        return CadenceBand.MONTHLY
    return CadenceBand.FORTNIGHTLY


def resolve_band(
    *,
    default_band: CadenceBand,
    auto_enabled: bool,
    history: ItemHistory,
    now: datetime | None = None,
) -> CadenceBand:
    """Full resolution — combines the baseline, Auto (if enabled),
    the Low/Out recency bump, and the Essential bump.

    See the module docstring for the ordering. Pure — every input the
    resolver needs is on the arguments; no repo access.
    """
    now_ = now or datetime.now(timezone.utc)

    band = default_band
    if auto_enabled:
        auto = auto_band_from_history(history.change_timestamps, now_)
        if auto is not None:
            band = auto

    bumps = 0
    if history.hit_low_or_out_recently:
        bumps += 1
    if history.is_essential:
        bumps += 1
    return _bump_faster(band, bumps)


# Public constants a caller may want (index, tests, DTOs).
__all__ = [
    "CadenceBand",
    "DEFAULT_BAND",
    "ItemHistory",
    "auto_band_from_history",
    "parse_band",
    "resolve_band",
]
