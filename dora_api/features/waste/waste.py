"""P2-06 — Expiry rescue + waste prevention.

  GET  /api/waste/rescue            — items expiring soon + recipes that
                                       use the most of them
  POST /api/waste/events            — log a discarded stock item
  GET  /api/waste/events?limit=N    — recent waste log
  GET  /api/waste/insights          — frequency + estimated value wasted

Rescue is *read-only* — it surfaces what's already in the data (expiry
dates + recipe ingredient links) and ranks recipes by how many of the
user's at-risk items they'd use. No manual entry required.

Waste events are *opt-in* — the user only writes a row when they tap
"Log as wasted" on the rescue page. We keep the row even if the stock
item is later deleted (FK SET NULL + denormalised name), so the
insights query survives pantry churn.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import List
from uuid import UUID

from flask import request
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import ShoppingListLine
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_waste_event import (
    StockItemWasteEvent, WASTE_REASON_OTHER, WASTE_REASON_VALUES,
)
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import WASTE_ROUTER
from dora_api.infrastructure.api_response import (bad_request, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# How far ahead "expiring soon" looks by default. Mirrors the assistant's
# _EXPIRY_HORIZON_DAYS so an item that's flagged here also appears in
# Dora's whats_expiring tool.
_DEFAULT_HORIZON_DAYS = 7
_MAX_HORIZON_DAYS = 60

# Cap returned rows everywhere — the rescue page is a one-glance UI, not
# a paginated list. The insights tool ditto.
_MAX_ROWS = 25


# ── /api/waste/rescue ────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ExpiringItemDto:
    stock_item_id: UUID
    name: str
    expiry_date: str
    days_until_expiry: int
    is_expired: bool
    stock_level_name: str | None
    estimated_value: float | None


@dataclass(frozen=True, slots=True)
class RescueRecipeDto:
    recipe_id: UUID
    name: str
    cook_time_minutes: int | None
    difficulty: str | None
    matching_expiring_items: List[str]
    matching_count: int
    missing_ingredients: List[str]
    is_favourite: bool


@dataclass(frozen=True, slots=True)
class WasteRescueDto:
    horizon_days: int
    items: List[ExpiringItemDto]
    recipes: List[RescueRecipeDto]


class GetWasteRescueHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, horizon_days: int) -> WasteRescueDto:
        horizon_days = max(0, min(horizon_days, _MAX_HORIZON_DAYS))
        today = date.today()
        cutoff = today + timedelta(days=horizon_days)

        items: list[StockItem] = (
            self.repository.get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .all(
                EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).is_not_null()
                & EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).lte(cutoff)
            )
        )
        items.sort(key=lambda i: i.expiry_date or date.max)

        # Cheapest-last-paid-price per stock item — pulled from archived
        # shopping list lines (P2-02 capture). Used as the "value at risk"
        # estimate so the rescue page can put a dollar figure on what's
        # about to spoil. Lines without a captured price are ignored;
        # zero is a worse default than "unknown".
        value_lookup: dict[UUID, float] = {}
        if items:
            item_ids = [i.id for i in items]
            lines = self.repository.get(ShoppingListLine).all(
                EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID)
                .in_(item_ids)
            )
            # Most recent priced line per item wins (lines aren't dated
            # individually, but a higher sequence on the same list is
            # newer enough for this guess). For honest-to-goodness
            # "last paid", reports/N6 + purchase_price_stats are the
            # authoritative path.
            for line in sorted(lines, key=lambda l: l.sequence):
                price = (
                    line.actual_unit_price
                    if line.actual_unit_price is not None
                    else line.picked_offer_price
                )
                if price is not None:
                    value_lookup[line.stock_item_id] = float(price)

        item_dtos: list[ExpiringItemDto] = []
        for item in items[:_MAX_ROWS]:
            days = (item.expiry_date - today).days if item.expiry_date else 0
            item_dtos.append(ExpiringItemDto(
                stock_item_id=item.id,
                name=item.name,
                expiry_date=item.expiry_date.isoformat() if item.expiry_date else "",
                days_until_expiry=days,
                is_expired=days < 0,
                stock_level_name=item.stock_level.name if item.stock_level else None,
                estimated_value=value_lookup.get(item.id),
            ))

        # Rank recipes by how many of the at-risk items they'd use.
        # We deliberately don't filter to "fully-cookable now" — the
        # point is to surface options that *help*, not options that
        # require a full pantry.
        at_risk_ids = {i.id for i in items}
        recipes: list[Recipe] = (
            self.repository.get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
            .then_include(RecipeIngredient.Fields.STOCK_ITEM)
            .then_include(StockItem.Fields.STOCK_LEVEL)
            .all()
        )
        ranked: list[RescueRecipeDto] = []
        for recipe in recipes:
            matches: list[str] = []
            missing: list[str] = []
            for ing in (recipe.ingredients or []):
                item = ing.stock_item
                if item is None:
                    continue
                if item.id in at_risk_ids:
                    matches.append(item.name)
                else:
                    level = item.stock_level
                    if level is None or level.sequence >= 3:
                        missing.append(item.name)
            if not matches:
                continue
            ranked.append(RescueRecipeDto(
                recipe_id=recipe.id,
                name=recipe.name,
                cook_time_minutes=recipe.cook_time_minutes,
                difficulty=recipe.difficulty,
                matching_expiring_items=matches,
                matching_count=len(matches),
                missing_ingredients=missing[:5],
                is_favourite=bool(recipe.is_favourite),
            ))
        # Most rescues first; favourites break ties so familiar food gets
        # the nudge over an obscure recipe with the same coverage.
        ranked.sort(key=lambda r: (-r.matching_count, not r.is_favourite, r.name))

        return WasteRescueDto(
            horizon_days=horizon_days,
            items=item_dtos,
            recipes=ranked[:_MAX_ROWS],
        )


@WASTE_ROUTER.route("/rescue", methods=["GET"])
def get_waste_rescue():
    _Logger = logging.getLogger(__name__)
    try:
        horizon = int(request.args.get("horizon_days", _DEFAULT_HORIZON_DAYS))
    except (TypeError, ValueError):
        horizon = _DEFAULT_HORIZON_DAYS
    dto = get_container().inject(GetWasteRescueHandler).handle(horizon)
    _Logger.debug(
        "waste rescue horizon=%d items=%d recipes=%d",
        dto.horizon_days, len(dto.items), len(dto.recipes),
    )
    return ok(dto)


# ── /api/waste/events ────────────────────────────────────────────────────

class LogWasteEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    reason: str = Field(min_length=1, max_length=32)
    quantity: int | None = Field(default=None, ge=0)
    estimated_value: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)
    # When true, the handler also bumps the stock level to "Out of
    # Stock" — most "I had to throw it out" cases mean the item is gone
    # from the pantry too. Defaults False so the caller is explicit.
    mark_out_of_stock: bool = False


@dataclass(slots=True)
class LogWasteEventResponse:
    event_id: UUID | None = None
    item_not_found: bool = False
    invalid_reason: bool = False


class LogWasteEventHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: LogWasteEventRequest) -> LogWasteEventResponse:
        if request.reason not in WASTE_REASON_VALUES:
            return LogWasteEventResponse(invalid_reason=True)

        item: StockItem | None = self.repository.get(StockItem).by_id(request.stock_item_id)
        if item is None:
            return LogWasteEventResponse(item_not_found=True)

        event = StockItemWasteEvent(
            stock_item_id=item.id,
            stock_item_name=item.name,
            reason=request.reason,
            quantity=request.quantity,
            estimated_value=(
                float(request.estimated_value)
                if request.estimated_value is not None else None
            ),
            note=request.note,
            occurred_at=datetime.now(timezone.utc),
        )
        self.repository.add(event)

        if request.mark_out_of_stock:
            out_level: StockLevel | None = self.repository.get(StockLevel).one(
                EntityField(StockLevel, StockLevel.Fields.NAME).eq("Out of Stock")
            )
            if out_level is not None:
                item.stock_level = out_level
                item.stock_level_last_updated = datetime.now(timezone.utc)

        self.repository.save_changes()
        return LogWasteEventResponse(event_id=event.id)


@WASTE_ROUTER.route("/events", methods=["POST"])
@has_request_body(LogWasteEventRequest)
def log_waste_event():
    _Logger = logging.getLogger(__name__)
    _Request: LogWasteEventRequest = get_request_body()
    _Response = get_container().inject(LogWasteEventHandler).handle(_Request)
    if _Response.invalid_reason:
        return bad_request(
            f"Invalid reason '{_Request.reason}'. Allowed: "
            f"{sorted(WASTE_REASON_VALUES)}"
        )
    if _Response.item_not_found:
        return not_found("StockItem", _Request.stock_item_id)
    _Logger.info(
        "Logged waste event %s (item=%s reason=%s)",
        _Response.event_id, _Request.stock_item_id, _Request.reason,
    )
    return ok({"event_id": _Response.event_id})


@WASTE_ROUTER.route("/events", methods=["GET"])
def list_waste_events():
    try:
        limit = max(1, min(int(request.args.get("limit", 25)), 200))
    except (TypeError, ValueError):
        limit = 25
    repo = SqlAlchemyRepository()
    events: list[StockItemWasteEvent] = repo.get(StockItemWasteEvent).all()
    events.sort(key=lambda e: e.occurred_at, reverse=True)
    return ok({
        "events": [
            {
                "event_id": str(e.id),
                "stock_item_id": str(e.stock_item_id) if e.stock_item_id else None,
                "stock_item_name": e.stock_item_name,
                "reason": e.reason,
                "quantity": e.quantity,
                "estimated_value": e.estimated_value,
                "note": e.note,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
            }
            for e in events[:limit]
        ],
    })


@WASTE_ROUTER.route("/events/<event_id>", methods=["DELETE"])
def delete_waste_event(event_id: str):
    _Logger = logging.getLogger(__name__)
    try:
        parsed = UUID(event_id)
    except (ValueError, TypeError):
        return bad_request("event_id must be a UUID.")
    repo = SqlAlchemyRepository()
    event = repo.get(StockItemWasteEvent).by_id(parsed)
    if event is None:
        return not_found("StockItemWasteEvent", parsed)
    repo.remove(event)
    repo.save_changes()
    _Logger.info("Deleted waste event %s", parsed)
    return no_content()


# ── /api/waste/insights ──────────────────────────────────────────────────

@WASTE_ROUTER.route("/insights", methods=["GET"])
def get_waste_insights():
    """Grouped-by-item summary plus an overall total. The frontend
    surfaces the top-wasted items as "buy smaller next time" candidates;
    the assistant uses the same rows to answer 'what am I wasting often?'.
    """
    try:
        window_days = int(request.args.get("window_days", 90))
    except (TypeError, ValueError):
        window_days = 90
    window_days = max(7, min(window_days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    repo = SqlAlchemyRepository()
    events: list[StockItemWasteEvent] = repo.get(StockItemWasteEvent).all(
        EntityField(StockItemWasteEvent, StockItemWasteEvent.Fields.OCCURRED_AT).gte(cutoff)
    )

    # Bucket by (stock_item_id, name) — the name is the denormalised
    # one captured at log time, so renames don't merge buckets and
    # deleted items still appear.
    buckets: dict[tuple, dict] = {}
    total_value = 0.0
    for event in events:
        key = (event.stock_item_id, event.stock_item_name)
        bucket = buckets.setdefault(key, {
            "stock_item_id": str(event.stock_item_id) if event.stock_item_id else None,
            "stock_item_name": event.stock_item_name,
            "event_count": 0,
            "total_quantity": 0,
            "estimated_value": 0.0,
            "reasons": {},
            "last_occurred_at": None,
        })
        bucket["event_count"] += 1
        if event.quantity:
            bucket["total_quantity"] += event.quantity
        if event.estimated_value:
            bucket["estimated_value"] += float(event.estimated_value)
            total_value += float(event.estimated_value)
        bucket["reasons"][event.reason] = bucket["reasons"].get(event.reason, 0) + 1
        # Track the latest event in the window so the SPA can surface
        # "last wasted X days ago" without re-querying.
        if (
            bucket["last_occurred_at"] is None
            or event.occurred_at > datetime.fromisoformat(bucket["last_occurred_at"])
        ):
            bucket["last_occurred_at"] = event.occurred_at.isoformat()

    rows = sorted(
        buckets.values(),
        key=lambda b: (-b["event_count"], -b["estimated_value"], b["stock_item_name"]),
    )
    for row in rows:
        row["estimated_value"] = round(row["estimated_value"], 2)

    return ok({
        "window_days": window_days,
        "total_events": len(events),
        "total_estimated_value": round(total_value, 2),
        "by_item": rows[:_MAX_ROWS],
    })
