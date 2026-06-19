"""X1 — Stocktake / Focused Review backend.

  GET  /api/stocktake/queue?limit=50          — items needing a check
  POST /api/stock-items/<id>/check            — bump last_checked_at only
  POST /api/stocktake/bulk-check              — body {ids}
  POST /api/shopping-lists/<id>/review/complete — bulk-set ticked items
                                                  to Well-Stocked (used by
                                                  the shopping-list review
                                                  mode).

The queue's ordering is:
  1. items with stocktake_alerts_are_enabled=True AND most-overdue first
  2. items never checked (last_checked_at IS NULL) treated as maximally
     overdue (so brand-new pantries surface immediately).
  3. tiebreak by name.

Per-item `days_until_stocktake_alert` is the per-item check cadence; an
item with `stocktake_alerts_are_enabled=False` is excluded from the
queue entirely (the user has opted it out — typically items they manage
manually).

Round-18 (2026-06-19) — engagement filter: an item must show signs the
user actually manages it before it enters the queue. Items the user
created and never touched ("nachos I don't keep in stock") would
previously surface immediately as "never-checked = maximally overdue";
now they're filtered out unless one of these signals fires:

  • Essential / Auto-add — explicit "this matters" flags.
  • Currently in stock (level sequence < OUT) — if it's actually
    present in the pantry, it's managed.
  • Ever opened — `opened_on` is non-null.
  • Level has been moved off the default — at least one
    `StockLevelChange` row exists (created on every level change).
  • On a shopping list now, or ever was — any `ShoppingListLine`
    row references this stock_item_id.

The existing overdue-days logic still applies on top; the engagement
filter just decides "is this worth surfacing at all".
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.stock_status import (OUT_OF_STOCK_SEQUENCE, StockStatus,
                                          level_for_status)
from dora_api.features.routers import STOCK_ITEM_ROUTER, STOCKTAKE_ROUTER
from dora_api.infrastructure.api_response import (bad_request, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ── Queue ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class StocktakeQueueItemDto:
    stock_item_id: UUID
    name: str
    stock_level_name: str | None
    stock_location_name: str | None
    days_until_stocktake_alert: int
    last_checked_at: str | None
    overdue_days: int


def _compute_overdue(item: StockItem, now: datetime) -> int:
    """Days the item is past its alert window. Items that have never
    been checked are treated as massively overdue so they surface first
    on a fresh install / new account."""
    window = item.days_until_stocktake_alert or 0
    if item.last_checked_at is None:
        # 9999 keeps never-checked items above any plausible window.
        return 9999
    elapsed = (now.date() - item.last_checked_at.date()).days
    return max(0, elapsed - window)


def _engaged_item_ids(item_ids: list[UUID]) -> tuple[set[UUID], set[UUID]]:
    """Pre-compute the engagement signals that require a DB lookup, in
    bulk — doing it per-item would explode into N+M queries on a big
    pantry. Returns (items_with_level_history, items_on_any_list).

    The remaining engagement signals (essential / auto-add / in-stock /
    opened) are plain attributes on `StockItem` and are read directly in
    the filter below.
    """
    if not item_ids:
        return set(), set()
    slc_table = db.metadata.tables["StockLevelChange"]
    line_table = db.metadata.tables["ShoppingListLine"]
    items_with_changes = {
        row[0] for row in db.session.execute(
            select(slc_table.c.stock_item_id)
            .where(slc_table.c.stock_item_id.in_(item_ids))
            .distinct()
        ).all()
    }
    items_on_lists = {
        row[0] for row in db.session.execute(
            select(line_table.c.stock_item_id)
            .where(line_table.c.stock_item_id.in_(item_ids))
            .distinct()
        ).all()
    }
    return items_with_changes, items_on_lists


def _is_engaged(
    item: StockItem,
    items_with_changes: set[UUID],
    items_on_lists: set[UUID],
) -> bool:
    """True when the item shows ANY sign the user actively manages it.
    Round-18 — see module docstring for the rationale."""
    if item.is_flagged or item.auto_add_when_low:
        return True
    if (
        item.stock_level is not None
        and item.stock_level.sequence < OUT_OF_STOCK_SEQUENCE
    ):
        return True
    if item.opened_on is not None:
        return True
    if item.id in items_with_changes:
        return True
    if item.id in items_on_lists:
        return True
    return False


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

    # Bulk-fetch the engagement signals so the per-item filter below stays
    # O(1) per item.
    items_with_changes, items_on_lists = _engaged_item_ids(
        [item.id for item in items]
    )

    overdue: list[tuple[int, StockItem]] = []
    for item in items:
        if not item.stocktake_alerts_are_enabled:
            continue
        if not _is_engaged(item, items_with_changes, items_on_lists):
            continue
        days = _compute_overdue(item, now)
        if days <= 0:
            continue
        overdue.append((days, item))

    overdue.sort(key=lambda pair: (
        -pair[0],
        pair[1].last_checked_at or datetime.min.replace(tzinfo=UTC),
        pair[1].name.lower(),
    ))
    total = len(overdue)
    page = overdue[:limit]

    dtos: List[StocktakeQueueItemDto] = []
    for days, item in page:
        # Cap the "never checked" sentinel at -1 so the SPA can render
        # "never checked" specially without subtracting 9999 from a day
        # count it'll only confuse a user.
        display_days = days if days < 9999 else -1
        dtos.append(StocktakeQueueItemDto(
            stock_item_id=item.id,
            name=item.name,
            stock_level_name=item.stock_level.name if item.stock_level else None,
            stock_location_name=(
                item.stock_location.name if item.stock_location else None
            ),
            days_until_stocktake_alert=item.days_until_stocktake_alert,
            last_checked_at=(
                item.last_checked_at.isoformat()
                if item.last_checked_at is not None else None
            ),
            overdue_days=display_days,
        ))
    return ok({"items": dtos, "total": total})


# ── /check (single) ────────────────────────────────────────────────────

@STOCK_ITEM_ROUTER.route("/<stock_item_id>/check", methods=["POST"])
def mark_stock_item_checked(stock_item_id: UUID):
    """Confirm the current level is still correct. Bumps last_checked_at
    only — does NOT touch stock_level_last_updated. Idempotent."""
    _Logger = logging.getLogger(__name__)
    repo = SqlAlchemyRepository()
    item = repo.get(StockItem).by_id(stock_item_id)
    if item is None:
        return not_found("StockItem", stock_item_id)
    item.last_checked_at = datetime.now(UTC)
    repo.save_changes()
    _Logger.debug("Stocktake check: %s", stock_item_id)
    return ok({
        "stock_item_id": str(stock_item_id),
        "last_checked_at": item.last_checked_at.isoformat(),
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
    result = db.session.execute(
        table.update().where(table.c.id.in_(body.ids)).values(last_checked_at=now)
    )
    db.session.commit()
    return ok({"checked": int(result.rowcount or 0)})


# ── /shopping-lists/<id>/review/complete ───────────────────────────────

class ReviewCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    set_well_stocked: bool = True


def _well_stocked_level_id(repo: SqlAlchemyRepository) -> UUID | None:
    """The seeded Well-Stocked level, resolved by status identity (sequence)
    rather than name — the UUID isn't stable across installs and the label may
    be renamed."""
    level = level_for_status(repo.get(StockLevel).all(), StockStatus.WELL_STOCKED)
    return level.id if level else None


from dora_api.features.routers import SHOPPING_LIST_ROUTER  # noqa: E402


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/review/complete", methods=["POST"])
@has_request_body(ReviewCompleteRequest)
def shopping_list_review_complete(shopping_list_id: UUID):
    """Mark every ticked item on this list as Well-Stocked AND bump both
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
        return ok({"set_well_stocked": 0, "checked": 0})

    now = datetime.now(UTC)
    checked_count = db.session.execute(
        item_table.update().where(item_table.c.id.in_(item_ids)).values(
            last_checked_at=now,
        )
    ).rowcount or 0

    set_count = 0
    if body.set_well_stocked:
        well_stocked_id = _well_stocked_level_id(repo)
        if well_stocked_id is None:
            return bad_request("Well-Stocked level not configured.")
        result = db.session.execute(
            item_table.update().where(item_table.c.id.in_(item_ids)).values(
                stock_level_id=well_stocked_id,
                stock_level_last_updated=now,
            )
        )
        set_count = int(result.rowcount or 0)

    db.session.commit()
    return ok({"set_well_stocked": set_count, "checked": int(checked_count)})
