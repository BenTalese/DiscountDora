"""X1 — Stocktake / Focused Review backend.

  GET  /api/stocktake/queue?limit=50          — items needing a check
  POST /api/stock-items/<id>/check            — bump last_checked_at only
  POST /api/stock-items/<id>/snooze           — Push 3 days
  POST /api/stocktake/bulk-check              — body {ids}
  POST /api/shopping-lists/<id>/review/complete — bulk-set ticked items
                                                  to Stocked (used by the
                                                  shopping-list review
                                                  mode).

Round-19 (2026-07-04) reboots the queue engine for the new stocktake
design (`docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md`). Two shifts:

1.  **Engagement gate — one honest question.** An item enters the queue
    only when it shows a *current* sign the user manages it. The old
    flag-based signals (`is_flagged`, `auto_add_when_low`) are dropped
    — a flag never forces a not-actually-kept item into the queue —
    and the two history signals gain a **60-day window** so an item
    touched a year ago no longer nags forever. Signals:
      • In stock right now (`stock_level.sequence < OUT`).
      • Ever opened (`opened_on` non-null).
      • Level adjusted in the last 60 days.
      • On a shopping list in the last 60 days (active list, or a
        closed list with `completed_at` inside the window).

2.  **Cadence bands + Auto self-tuning.** Per-item overdue is measured
    against a *resolved band* (Weekly/Fortnightly/Monthly, see
    `cadence.py`). Baseline = the global
    `AppSetting.stocktake_default_cadence_band`; Auto (on by default)
    overrides from movement history; Low/Out in the last 14 days bumps
    one band faster; Essential (`is_flagged`) bumps one more.
    Change-level *implicitly* checks the item (already done in
    `update_stock_item.py`), so the grace-period baseline for a
    never-checked item is `COALESCE(last_checked_at,
    stock_level_last_updated)` — the "when did the user last touch
    this" timestamp. No 9999 sentinel.

    Push (snooze) filters out items whose `snoozed_until > now`;
    Mute is unchanged (`stocktake_alerts_are_enabled=False` still
    excludes).
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DONE,
)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.stock_status import (LOW_STOCK_SEQUENCE,
                                          OUT_OF_STOCK_SEQUENCE, StockStatus,
                                          level_for_status)
from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.routers import STOCK_ITEM_ROUTER, STOCKTAKE_ROUTER
from dora_api.features.stocktake.cadence import (CadenceBand, ItemHistory,
                                                 parse_band, resolve_band)
from dora_api.infrastructure.api_response import (bad_request, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ── Windows ────────────────────────────────────────────────────────────
# History-signal windows for the engagement gate + Auto's Low/Out bump.
# All in one place so the queue, the tests, and any future assistant
# tool resolve to the same numbers (R-003).
_ENGAGEMENT_WINDOW_DAYS = 60
_LOW_OUT_BUMP_WINDOW_DAYS = 14
_AUTO_HISTORY_WINDOW_DAYS = 90  # mirrors cadence.py's _AUTO_HISTORY_WINDOW_DAYS

# Push (snooze) window — fixed 3 days per §5 (open-decision resolved).
_SNOOZE_DAYS = 3


# ── Queue DTO ──────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class StocktakeQueueItemDto:
    stock_item_id: UUID
    name: str
    stock_level_name: str | None
    stock_location_name: str | None
    # Resolved band the runner shows next to the item ("checked every
    # week / fortnight / month"). Server-owned (R-003) — the SPA never
    # re-derives a band.
    cadence_band: str
    # Effective cadence in days (matches `cadence_band` — sent for
    # convenience so the SPA doesn't need to map the string itself).
    cadence_days: int
    last_checked_at: str | None
    overdue_days: int


# ── Overdue baseline ───────────────────────────────────────────────────

def _overdue_baseline(item: StockItem) -> datetime | None:
    """The timestamp we measure overdue from.

    `COALESCE(last_checked_at, stock_level_last_updated)` — "when did
    the user last touch this?" Change-level bumps `last_checked_at`
    (see `update_stock_item.py`), so any item the user has ever
    touched has a `last_checked_at`; only a truly never-touched item
    falls back to `stock_level_last_updated` (which equals its
    creation moment, since a StockItem is always created with a
    level).

    Replaces the old 9999-sentinel behaviour: brand-new items now
    have a natural grace period equal to one cadence band, not "top
    of the queue on turn zero".
    """
    if item.last_checked_at is not None:
        return item.last_checked_at
    return item.stock_level_last_updated


def _compute_overdue_days(
    item: StockItem, band_days: int, now: datetime,
) -> int:
    """Days past the resolved band since the overdue baseline. 0 if
    the item is not yet due; `_overdue_baseline` returning None (a
    genuinely-orphan row with no level) also reads as 0 — the item
    just doesn't surface, which is the safe fallback."""
    baseline = _overdue_baseline(item)
    if baseline is None:
        return 0
    elapsed = (now.date() - baseline.date()).days
    return max(0, elapsed - band_days)


# ── Engagement gate ────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class _EngagementSignals:
    """Bulk pre-computed signals for the engagement gate + Auto tuner.
    Assembling per-item would explode into N+M queries on a big
    pantry."""
    items_with_recent_level_change: set[UUID]
    items_on_recent_list: set[UUID]
    # Per-item trailing-90d list of change timestamps for the Auto
    # self-tuner (`cadence.py::auto_band_from_history`).
    change_timestamps_by_item: dict[UUID, list[datetime]]
    # Per-item flag: any StockLevelChange in the last
    # _LOW_OUT_BUMP_WINDOW_DAYS whose target level's sequence is ≥
    # LOW_STOCK. Bumps one band faster.
    items_hit_low_or_out_recently: set[UUID]


def _gather_engagement_signals(
    item_ids: list[UUID],
    now: datetime,
) -> _EngagementSignals:
    empty = _EngagementSignals(set(), set(), {}, set())
    if not item_ids:
        return empty

    slc_table = db.metadata.tables["StockLevelChange"]
    sl_table = db.metadata.tables["StockLevel"]
    line_table = db.metadata.tables["ShoppingListLine"]
    list_table = db.metadata.tables["ShoppingList"]

    engagement_cutoff = now - timedelta(days=_ENGAGEMENT_WINDOW_DAYS)
    auto_history_cutoff = now - timedelta(days=_AUTO_HISTORY_WINDOW_DAYS)
    low_out_cutoff = now - timedelta(days=_LOW_OUT_BUMP_WINDOW_DAYS)

    # Level-change rows for the trailing Auto-history window (which is
    # a superset of the engagement window, so one query covers both).
    # Join levels to know each change's sequence for the Low/Out bump.
    change_rows = db.session.execute(
        select(
            slc_table.c.stock_item_id,
            slc_table.c.changed_at,
            sl_table.c.sequence,
        )
        .select_from(
            slc_table.outerjoin(
                sl_table, slc_table.c.stock_level_id == sl_table.c.id,
            )
        )
        .where(
            slc_table.c.stock_item_id.in_(item_ids),
            slc_table.c.changed_at >= auto_history_cutoff,
        )
    ).all()

    change_timestamps_by_item: dict[UUID, list[datetime]] = {}
    items_with_recent_level_change: set[UUID] = set()
    items_hit_low_or_out_recently: set[UUID] = set()
    for stock_item_id, changed_at, seq in change_rows:
        change_timestamps_by_item.setdefault(stock_item_id, []).append(changed_at)
        if changed_at >= engagement_cutoff:
            items_with_recent_level_change.add(stock_item_id)
        if (
            seq is not None
            and seq >= LOW_STOCK_SEQUENCE
            and changed_at >= low_out_cutoff
        ):
            items_hit_low_or_out_recently.add(stock_item_id)

    # Shopping-list membership within the engagement window. Active
    # lists (status ≠ 'done') always qualify; closed lists count if
    # their completed_at is within the window. This is what makes
    # "on a list once 5 months ago" stop nagging.
    list_rows = db.session.execute(
        select(line_table.c.stock_item_id)
        .select_from(
            line_table.join(
                list_table,
                line_table.c.shopping_list_id == list_table.c.id,
            )
        )
        .where(
            line_table.c.stock_item_id.in_(item_ids),
            (
                (list_table.c.status != SHOPPING_LIST_STATUS_DONE)
                | (list_table.c.completed_at >= engagement_cutoff)
            ),
        )
        .distinct()
    ).all()
    items_on_recent_list = {row[0] for row in list_rows}

    return _EngagementSignals(
        items_with_recent_level_change=items_with_recent_level_change,
        items_on_recent_list=items_on_recent_list,
        change_timestamps_by_item=change_timestamps_by_item,
        items_hit_low_or_out_recently=items_hit_low_or_out_recently,
    )


def _is_engaged(item: StockItem, signals: _EngagementSignals) -> bool:
    """The single question: *do you actually keep this item?*

    Any one of four in-play signs is enough. Flag columns
    (`is_flagged` / `auto_add_when_low`) are **not** signals here —
    they cover how an in-play item is treated, not whether the item
    is in play at all. See §2 of the brief.
    """
    if (
        item.stock_level is not None
        and item.stock_level.sequence < OUT_OF_STOCK_SEQUENCE
    ):
        return True
    if item.opened_on is not None:
        return True
    if item.id in signals.items_with_recent_level_change:
        return True
    if item.id in signals.items_on_recent_list:
        return True
    return False


# ── Shared overdue resolver ────────────────────────────────────────────
# The single authority for "is this item currently overdue for a
# stocktake, and by how much?" — used by the queue endpoint below AND
# by the alerts feed (`alerts/get_alerts.py`) so the bell + the runner
# never surface different sets of items (R-003). Filters for mute +
# push (snooze) + engagement gate in one pass, so callers get only
# the items they should actually surface.


@dataclass(frozen=True, slots=True)
class OverdueInfo:
    band: CadenceBand
    days: int  # whole days past the resolved band's window; always ≥ 1.


def resolve_overdue_map(
    items: list[StockItem],
    now: datetime | None = None,
) -> dict[UUID, OverdueInfo]:
    """Return `{stock_item_id: OverdueInfo}` for every item that is
    currently overdue for a stocktake — with mute, push (snooze) and
    the engagement gate already applied, and the cadence band already
    resolved (global default → Auto → Low/Out bump → Essential bump).

    Bulk-fetches all engagement signals in two queries regardless of
    input size, so the whole map costs the same as one queue endpoint
    call — safe to invoke from the alerts feed on every request.

    Pass `items` with `stock_level` loaded (the engagement gate needs
    the sequence). Repo access + AppSetting read happen inside — the
    caller doesn't need to thread them in.
    """
    now_ = now or datetime.now(UTC)
    if not items:
        return {}
    repo = SqlAlchemyRepository()
    app_setting = get_or_create_app_setting(repo)
    default_band = parse_band(
        getattr(app_setting, "stocktake_default_cadence_band", None)
    )
    auto_enabled = bool(
        getattr(app_setting, "stocktake_auto_tuning_enabled", True)
    )
    signals = _gather_engagement_signals([item.id for item in items], now_)
    result: dict[UUID, OverdueInfo] = {}
    for item in items:
        if not item.stocktake_alerts_are_enabled:
            continue
        if item.snoozed_until is not None and item.snoozed_until > now_:
            continue
        if not _is_engaged(item, signals):
            continue
        history = ItemHistory(
            change_timestamps=tuple(
                signals.change_timestamps_by_item.get(item.id, ())
            ),
            hit_low_or_out_recently=item.id in signals.items_hit_low_or_out_recently,
            is_essential=bool(item.is_flagged),
        )
        band = resolve_band(
            default_band=default_band,
            auto_enabled=auto_enabled,
            history=history,
            now=now_,
        )
        days = _compute_overdue_days(item, band.days, now_)
        if days <= 0:
            continue
        result[item.id] = OverdueInfo(band=band, days=days)
    return result


# ── Queue endpoint ─────────────────────────────────────────────────────

@STOCKTAKE_ROUTER.route("/queue", methods=["GET"])
def get_stocktake_queue():
    from flask import request
    try:
        limit = int(request.args.get("limit", "50"))
    except ValueError:
        return bad_request("limit must be an integer.")
    if limit < 1 or limit > 500:
        return bad_request("limit must be between 1 and 500.")

    repo = SqlAlchemyRepository()
    items = (
        repo.get(StockItem)
        .include("stock_level")
        .include("stock_location")
        .all()
    )
    now = datetime.now(UTC)

    overdue_map = resolve_overdue_map(items, now)
    # Materialise as (days, band, item) tuples so the sort key can
    # tiebreak on baseline + name without re-looking-up per row.
    overdue: list[tuple[int, CadenceBand, StockItem]] = [
        (info.days, info.band, item)
        for item in items
        if (info := overdue_map.get(item.id)) is not None
    ]

    overdue.sort(key=lambda triple: (
        -triple[0],
        _overdue_baseline(triple[2]) or datetime.min.replace(tzinfo=UTC),
        triple[2].name.lower(),
    ))
    total = len(overdue)
    page = overdue[:limit]

    dtos: List[StocktakeQueueItemDto] = []
    for days, band, item in page:
        dtos.append(StocktakeQueueItemDto(
            stock_item_id=item.id,
            name=item.name,
            stock_level_name=item.stock_level.name if item.stock_level else None,
            stock_location_name=(
                item.stock_location.name if item.stock_location else None
            ),
            cadence_band=band.value,
            cadence_days=band.days,
            last_checked_at=(
                item.last_checked_at.isoformat()
                if item.last_checked_at is not None else None
            ),
            overdue_days=days,
        ))
    return ok({"items": dtos, "total": total})


# ── /check (single) ────────────────────────────────────────────────────

@STOCK_ITEM_ROUTER.route("/<stock_item_id>/check", methods=["POST"])
def mark_stock_item_checked(stock_item_id: UUID):
    """Confirm the current level is still correct. Bumps last_checked_at
    AND clears any active Push snooze (a Check is a stronger claim than
    a Push — the user just looked). Does NOT touch stock_level_last_
    updated. Idempotent."""
    _Logger = logging.getLogger(__name__)
    repo = SqlAlchemyRepository()
    item = repo.get(StockItem).by_id(stock_item_id)
    if item is None:
        return not_found("StockItem", stock_item_id)
    item.last_checked_at = datetime.now(UTC)
    item.snoozed_until = None
    repo.save_changes()
    _Logger.debug("Stocktake check: %s", stock_item_id)
    return ok({
        "stock_item_id": str(stock_item_id),
        "last_checked_at": item.last_checked_at.isoformat(),
    })


# ── /snooze (single) — Push 3 days ────────────────────────────────────

@STOCK_ITEM_ROUTER.route("/<stock_item_id>/snooze", methods=["POST"])
def snooze_stock_item(stock_item_id: UUID):
    """PROPOSAL_STOCKTAKE_MODE §5 — the honest defer. Hides the item
    from the queue for the fixed 3-day window. Deliberately does NOT
    bump last_checked_at — Push makes no claim the stock is right, so
    a Push must not corrupt the "when was this last verified" audit."""
    _Logger = logging.getLogger(__name__)
    repo = SqlAlchemyRepository()
    item = repo.get(StockItem).by_id(stock_item_id)
    if item is None:
        return not_found("StockItem", stock_item_id)
    item.snoozed_until = datetime.now(UTC) + timedelta(days=_SNOOZE_DAYS)
    repo.save_changes()
    _Logger.debug(
        "Stocktake snooze: %s until %s", stock_item_id, item.snoozed_until,
    )
    return ok({
        "stock_item_id": str(stock_item_id),
        "snoozed_until": item.snoozed_until.isoformat(),
    })


# ── /bulk-check ────────────────────────────────────────────────────────

class BulkCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ids: list[UUID] = Field(min_length=1, max_length=500)


@STOCKTAKE_ROUTER.route("/bulk-check", methods=["POST"])
@has_request_body(BulkCheckRequest)
def bulk_check():
    body: BulkCheckRequest = get_request_body()
    table = db.metadata.tables["StockItem"]
    now = datetime.now(UTC)
    # Bulk-check also clears any active snoozes, mirroring the
    # single-item /check path — a Check is stronger than a Push.
    result = db.session.execute(
        table.update()
        .where(table.c.id.in_(body.ids))
        .values(last_checked_at=now, snoozed_until=None)
    )
    db.session.commit()
    return ok({"checked": int(result.rowcount or 0)})


# ── /shopping-lists/<id>/review/complete ───────────────────────────────

class ReviewCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    set_stocked: bool = True


def _stocked_level_id(repo: SqlAlchemyRepository) -> UUID | None:
    """The seeded Stocked level, resolved by status identity (sequence)
    rather than name — the UUID isn't stable across installs and the label may
    be renamed."""
    level = level_for_status(repo.get(StockLevel).all(), StockStatus.STOCKED)
    return level.id if level else None


from dora_api.features.routers import SHOPPING_LIST_ROUTER  # noqa: E402


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/review/complete", methods=["POST"])
@has_request_body(ReviewCompleteRequest)
def shopping_list_review_complete(shopping_list_id: UUID):
    """Mark every ticked item on this list as Stocked AND bump both
    timestamps. Mirrors the existing finish-shopping flow but without
    archiving the list."""
    body: ReviewCompleteRequest = get_request_body()
    repo = SqlAlchemyRepository()

    line_table = db.metadata.tables["ShoppingListLine"]
    item_table = db.metadata.tables["StockItem"]
    list_table = db.metadata.tables["ShoppingList"]

    from sqlalchemy import select
    if db.session.execute(
        select(list_table.c.id).where(list_table.c.id == shopping_list_id)
    ).first() is None:
        return not_found("ShoppingList", shopping_list_id)

    ticked_rows = db.session.execute(
        select(line_table.c.stock_item_id).where(
            line_table.c.shopping_list_id == shopping_list_id,
            line_table.c.is_ticked == True,  # noqa: E712
        )
    ).all()
    item_ids = [r[0] for r in ticked_rows]
    if not item_ids:
        return ok({"set_stocked": 0, "checked": 0})

    now = datetime.now(UTC)
    checked_count = db.session.execute(
        item_table.update().where(item_table.c.id.in_(item_ids)).values(
            last_checked_at=now,
            snoozed_until=None,
        )
    ).rowcount or 0

    set_count = 0
    if body.set_stocked:
        stocked_id = _stocked_level_id(repo)
        if stocked_id is None:
            return bad_request("Stocked level not configured.")
        result = db.session.execute(
            item_table.update().where(item_table.c.id.in_(item_ids)).values(
                stock_level_id=stocked_id,
                stock_level_last_updated=now,
            )
        )
        set_count = int(result.rowcount or 0)

    db.session.commit()
    return ok({"set_stocked": set_count, "checked": int(checked_count)})
