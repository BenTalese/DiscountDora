
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
    # The linked product the user prefers to buy. Present-but-None clears it.
    preferred_product_id: UUID | None = None


@dataclass(slots=True)
class UpdateStockItemResponse:  # noqa: D401
    stock_item_already_exists: bool = False
    stock_item_not_found: bool = False
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False
    stock_group_not_found: bool = False


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
            # the overview can show "updated X ago" honestly.
            _StockItem.stock_level_last_updated = datetime.now(UTC)
            # Append to the level-change history when the level actually moves.
            if _StockLevel.id != _PreviousLevelId:
                self.repository.add(StockLevelChange(
                    stock_item_id = _StockItem.id,
                    stock_level_id = _StockLevel.id,
                    stock_level_name = _StockLevel.name,
                    changed_at = datetime.now(UTC),
                ))

        if "stock_location_id" in _SetFields:
            if request.stock_location_id is None:
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

        if "is_flagged" in _SetFields and request.is_flagged is not None:
            _StockItem.is_flagged = request.is_flagged

        if "auto_add_when_low" in _SetFields and request.auto_add_when_low is not None:
            _StockItem.auto_add_when_low = request.auto_add_when_low

        # stock_group: nullable FK, so a present-but-None value means
        # "clear the group". Same shape as stock_location_id above.
        if "stock_group_id" in _SetFields:
            if request.stock_group_id is None:
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

        # Preferred product: present-but-None clears it. No strict validation
        # that it's a linked product — pre-release, the UI only offers linked
        # products as options.
        if "preferred_product_id" in _SetFields:
            _StockItem.preferred_product_id = request.preferred_product_id

        # Auto-add hook: if this update transitioned the item from "ok" to
        # low-or-out and `auto_add_when_low` is set, drop it onto the
        # current primary list. Skipped silently if there's no primary or
        # the item is already on it — the hook is a convenience, not a
        # contract.
        _NewLevelSeq: int | None = (
            _StockItem.stock_level.sequence if _StockItem.stock_level else None
        )
        if (
            _StockItem.auto_add_when_low
            and _NewLevelSeq is not None
            and _NewLevelSeq >= 2  # 2 = Low, 3 = Out (see seed)
            and (_PreviousLevelSeq is None or _PreviousLevelSeq < 2)
        ):
            self._try_quick_add_to_primary(_StockItem)

        self.repository.save_changes()
        return UpdateStockItemResponse()

    def _try_quick_add_to_primary(self, stock_item: StockItem) -> None:
        """Adds the stock item to the current primary shopping list.

        Imported locally because pulling the shopping-list entities at
        module import time would create an import cycle (the shopping list
        handlers already depend on StockItem).
        """
        from dora_api.domain.entities.shopping_list import (
            ShoppingList, ShoppingListLine,
        )

        primary: ShoppingList | None = self.repository.get(ShoppingList).one(
            EntityField(ShoppingList, ShoppingList.Fields.IS_PRIMARY).eq(True)
            & EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(False)
        )
        if primary is None:
            return

        existing = self.repository.get(ShoppingListLine).one(
            EntityField(ShoppingListLine, "shopping_list_id").eq(primary.id)
            & EntityField(ShoppingListLine, "stock_item_id").eq(stock_item.id)
        )
        if existing is not None:
            return

        siblings = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(primary.id)
        )
        next_sequence = (max((l.sequence for l in siblings), default=-1)) + 1
        self.repository.add(ShoppingListLine(
            shopping_list_id = primary.id,
            stock_item_id = stock_item.id,
            quantity = 1,
            sequence = next_sequence,
        ))


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
    return no_content()
