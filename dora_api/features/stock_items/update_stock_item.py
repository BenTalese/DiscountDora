
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  entity_existence_failure,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateStockItemRequest(BaseModel):
    """Partial update — only fields present in the request body are applied.

    `stock_level_id` and `name` have special handling. Everything else is
    treated as a straight setattr.
    """
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default = None, min_length = 1, max_length = 255)
    notes: str | None = Field(default = None, max_length = 255)
    days_until_stocktake_alert: int | None = Field(default = None, ge = 0)
    stocktake_alerts_are_enabled: bool | None = None
    stock_level_id: UUID | None = None
    stock_location_id: UUID | None = None
    stock_group_id: UUID | None = None
    expiry_date: date | None = None
    is_flagged: bool | None = None
    auto_add_when_low: bool | None = None
    is_open: bool | None = None
    # Explicit override for `opened_on` — usually set automatically when
    # `is_open` flips True, but the spec also wants a manual edit path
    # ("I can edit the date a stock item was opened on…").
    opened_on: date | None = None
    # C-1 Chunk 6 / FU-033 — data-URL string to set the image, null to
    # clear, omit to leave untouched. Mirrors the recipe-update contract.
    image: str | None = Field(default = None, max_length = 6_000_000)
    # FU-189 — usual store hint. Send a UUID to bind, omit to leave alone;
    # send `clear_usual_store=true` to blank an existing value (the same
    # clear-vs-unset pattern as ShoppingListLine fields).
    usual_store_id: UUID | None = None
    clear_usual_store: bool = False
    # Explicit clear flags for location and group — the relationships are
    # mapped `lazy="noload"`, so assigning the relationship-side to None
    # is a silent no-op (the FK column never goes dirty). The clear-flag
    # path drives the FK column directly, sidestepping the SQLAlchemy
    # quirk so the picker's X button actually persists.
    clear_stock_location: bool = False
    clear_stock_group: bool = False


@dataclass(slots=True)
class UpdateStockItemResponse:  # noqa: D401
    stock_item_already_exists: bool = False
    stock_item_not_found: bool = False
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False
    stock_group_not_found: bool = False
    # X5: when the auto_add_when_low trigger fires, the API needs to know
    # so it can surface an undoable "Tomato Soup auto-added to <list>"
    # notification. None when no auto-add happened.
    auto_added_line_id: UUID | None = None
    auto_added_to_list_id: UUID | None = None


class UpdateStockItemHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateStockItemRequest, stock_item_id: UUID) -> UpdateStockItemResponse:
        _StockItem: StockItem | None = self.repository.get(StockItem).by_id(stock_item_id)
        if not _StockItem:
            return UpdateStockItemResponse(stock_item_not_found = True)

        _SetFields = request.model_fields_set

        # Capture the *previous* stock level sequence so we can detect the
        # specific transition the auto-add hook cares about (something
        # well-stocked dropping to low/out).
        _PreviousLevelSeq: int | None = (
            _StockItem.stock_level.sequence if _StockItem.stock_level else None
        )
        _PreviousLevelId = _StockItem.stock_level.id if _StockItem.stock_level else None

        if "stock_level_id" in _SetFields and request.stock_level_id is not None:
            _StockLevel = self.repository.get(StockLevel).by_id(request.stock_level_id)
            if not _StockLevel:
                return UpdateStockItemResponse(stock_level_not_found=True)
            _StockItem.stock_level = _StockLevel
            # Stock-level changes always touch the last-updated timestamp so
            # the overview can show "updated X ago" honestly. X1: also bump
            # last_checked_at — a level change is implicitly a check of the
            # current state too.
            _Now = datetime.now(UTC)
            _StockItem.stock_level_last_updated = _Now
            _StockItem.last_checked_at = _Now
            # Append to the level-change history when the level actually moves.
            if _StockLevel.id != _PreviousLevelId:
                self.repository.add(StockLevelChange(
                    stock_item_id = _StockItem.id,
                    stock_level_id = _StockLevel.id,
                    stock_level_name = _StockLevel.name,
                    changed_at = datetime.now(UTC),
                ))

        # stock_location: same lazy="noload" trap as stock_group below — a
        # relationship-only None assignment doesn't dirty the FK column, so
        # set `_stock_location_id` directly when clearing.
        if request.clear_stock_location:
            _StockItem._stock_location_id = None
            _StockItem.stock_location = None
        elif "stock_location_id" in _SetFields:
            if request.stock_location_id is None:
                _StockItem._stock_location_id = None
                _StockItem.stock_location = None
            else:
                _StockLocation = self.repository.get(StockLocation).by_id(request.stock_location_id)
                if not _StockLocation:
                    return UpdateStockItemResponse(stock_location_not_found=True)
                _StockItem.stock_location = _StockLocation

        if "name" in _SetFields and request.name is not None:
            _NameField = EntityField(StockItem, StockItem.Fields.NAME)
            _SameName: StockItem | None = (
                self.repository.get(StockItem).one(_NameField.eq(request.name))
            )
            if _SameName and _SameName.id != stock_item_id:
                return UpdateStockItemResponse(stock_item_already_exists=True)
            _StockItem.name = request.name

        if "notes" in _SetFields:
            _StockItem.notes = request.notes

        if "days_until_stocktake_alert" in _SetFields and request.days_until_stocktake_alert is not None:
            _StockItem.days_until_stocktake_alert = request.days_until_stocktake_alert

        if "stocktake_alerts_are_enabled" in _SetFields and request.stocktake_alerts_are_enabled is not None:
            _StockItem.stocktake_alerts_are_enabled = request.stocktake_alerts_are_enabled

        if "expiry_date" in _SetFields:
            _StockItem.expiry_date = request.expiry_date

        # C-1 Chunk 6 / FU-033 — explicit null clears, data-URL string sets.
        if "image" in _SetFields:
            _StockItem.image = (
                request.image.encode("utf-8") if request.image else None
            )

        if "is_flagged" in _SetFields and request.is_flagged is not None:
            _StockItem.is_flagged = request.is_flagged

        if "auto_add_when_low" in _SetFields and request.auto_add_when_low is not None:
            _StockItem.auto_add_when_low = request.auto_add_when_low

        # FU-189 — usual store hint. Clear flag wins over a present-but-None.
        # We don't validate the target Store exists here: the FK has SET NULL
        # ondelete, so a stale id silently degrades; the SPA picker only
        # surfaces actual rows so the bad-write path requires hand-crafting.
        if request.clear_usual_store:
            _StockItem.usual_store_id = None
        elif "usual_store_id" in _SetFields and request.usual_store_id is not None:
            _StockItem.usual_store_id = request.usual_store_id

        # stock_group: nullable FK with the same lazy="noload" trap — see
        # the comment on stock_location above. Explicit `clear_stock_group`
        # is the SPA's canonical clear path; the present-but-None branch
        # also writes the FK column so a stray null still works.
        if request.clear_stock_group:
            _StockItem._stock_group_id = None
            _StockItem.stock_group = None
        elif "stock_group_id" in _SetFields:
            if request.stock_group_id is None:
                _StockItem._stock_group_id = None
                _StockItem.stock_group = None
            else:
                from dora_api.domain.entities.stock_group import StockGroup
                _Group = self.repository.get(StockGroup).by_id(request.stock_group_id)
                if _Group is None:
                    return UpdateStockItemResponse(stock_group_not_found=True)
                _StockItem.stock_group = _Group

        # `is_open` flipping True records today's date in `opened_on`
        # automatically (the spec). Flipping back to False clears it.
        # An explicit `opened_on` value in the same request overrides the
        # auto-set, supporting the "edit the opened date" case.
        if "is_open" in _SetFields and request.is_open is not None:
            previous_open = bool(_StockItem.is_open)
            _StockItem.is_open = request.is_open
            if request.is_open and not previous_open:
                from datetime import date as _date
                _StockItem.opened_on = _date.today()
            elif not request.is_open:
                _StockItem.opened_on = None

        if "opened_on" in _SetFields:
            _StockItem.opened_on = request.opened_on

        # Auto-add hook: if this update transitioned the item from "ok" to
        # low-or-out and `auto_add_when_low` is set, drop it onto the
        # current primary list. Skipped silently if there's no primary,
        # or if the item is already on ANY non-archived list — the user
        # already knows; double-add would be annoying.
        _NewLevelSeq: int | None = (
            _StockItem.stock_level.sequence if _StockItem.stock_level else None
        )
        _AutoAddResult: tuple[UUID, UUID] | None = None
        if (
            _StockItem.auto_add_when_low
            and _NewLevelSeq is not None
            and _NewLevelSeq >= 2  # 2 = Low, 3 = Out (see seed)
            and (_PreviousLevelSeq is None or _PreviousLevelSeq < 2)
        ):
            _AutoAddResult = self._try_auto_add(_StockItem)

        self.repository.save_changes()
        if _AutoAddResult is not None:
            line_id, list_id = _AutoAddResult
            return UpdateStockItemResponse(
                auto_added_line_id=line_id,
                auto_added_to_list_id=list_id,
            )
        return UpdateStockItemResponse()

    def _try_auto_add(self, stock_item: StockItem) -> tuple[UUID, UUID] | None:
        """Adds the stock item to the primary shopping list, X5-style.

        Returns (line_id, list_id) on a successful add; None when skipped
        (no primary, already on any active list, etc). Imported locally
        because pulling shopping-list entities at module import time
        creates a cycle.
        """
        from dora_api.domain.entities.shopping_list import (
            ADDED_VIA_AUTO_LOW_STOCK,
            SHOPPING_LIST_STATUS_DONE,
            ShoppingList,
            ShoppingListLine,
        )

        # Already on ANY active list? Skip — the user already knows.
        active_lists: list[ShoppingList] = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
        )
        active_ids = [l.id for l in active_lists]
        if active_ids:
            on_any = self.repository.get(ShoppingListLine).one(
                EntityField(ShoppingListLine, "stock_item_id").eq(stock_item.id)
                & EntityField(ShoppingListLine, "shopping_list_id").in_(active_ids)
            )
            if on_any is not None:
                return None

        # Auto-add only when there's an unambiguous DRAFT target — if the user
        # has 0 or 2+ drafts, the cart button still does the right thing on the
        # next manual click; we don't silently pick one.
        from dora_api.features.shopping_lists.primary_target_resolver import \
            resolve_primary_target
        outcome = resolve_primary_target(active_lists)
        if outcome.kind != "single":
            return None
        target = next(
            (l for l in active_lists if l.id == outcome.target_list_id), None
        )
        if target is None:
            return None

        siblings = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(target.id)
        )
        next_sequence = (max((l.sequence for l in siblings), default=-1)) + 1
        line = ShoppingListLine(
            shopping_list_id=target.id,
            stock_item_id=stock_item.id,
            quantity=1,
            sequence=next_sequence,
            added_via=ADDED_VIA_AUTO_LOW_STOCK,
            added_at=datetime.now(UTC),
        )
        self.repository.add(line)
        return (line.id, target.id)


@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["PATCH"])
@has_request_body(UpdateStockItemRequest)
def update_stock_item(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update stock item.")
    _Handler = get_container().inject(UpdateStockItemHandler)
    _Request: UpdateStockItemRequest = get_request_body()
    _Response = _Handler.handle(_Request, stock_item_id)

    if _Response.stock_item_not_found:
        _Logger.warning(f"Stock item not found with ID: {stock_item_id}")
        return not_found(StockItem.__name__, stock_item_id)

    if _Response.stock_item_already_exists:
        _Logger.warning(f"Stock item already exists with name: {_Request.name}")
        return business_rule_violation(f"A stock item with the name '{_Request.name}' already exists.")

    if _Response.stock_level_not_found and _Request.stock_level_id is not None:
        _Logger.warning(f"Stock level not found: {_Request.stock_level_id}")
        return entity_existence_failure(StockLevel.__name__, "stock_level_id", _Request.stock_level_id)

    if _Response.stock_location_not_found and _Request.stock_location_id is not None:
        _Logger.warning(f"Stock location not found: {_Request.stock_location_id}")
        return entity_existence_failure(StockLocation.__name__, "stock_location_id", _Request.stock_location_id)

    if _Response.stock_group_not_found and _Request.stock_group_id is not None:
        _Logger.warning(f"Stock group not found: {_Request.stock_group_id}")
        from dora_api.domain.entities.stock_group import StockGroup
        return entity_existence_failure(
            StockGroup.__name__, "stock_group_id", _Request.stock_group_id,
        )

    _Logger.info(f"Successfully updated stock item with ID: {stock_item_id}")
    # X5: if the auto_add_when_low trigger fired, return a 200 with a
    # minimal body so the UI can pop the undoable "auto-added to <list>"
    # toast. No trigger → keep the original 204 for simplicity.
    if _Response.auto_added_line_id is not None:
        from dora_api.infrastructure.api_response import ok
        return ok({
            "auto_added": {
                "line_id": _Response.auto_added_line_id,
                "shopping_list_id": _Response.auto_added_to_list_id,
            },
        })
    return no_content()
