"""POST /api/stock-items/restore — recreate a previously-deleted stock
item from a client-held snapshot.

Used by the global Undo flow (F5). Distinct from POST /stock-items
(which mints a fresh id and is what users hit when creating an item)
because the inverse of a delete needs to preserve the original id so
references (recipe ingredients, shopping list lines, product links)
still point somewhere sensible — even when the references themselves
have already been cascaded away by the prior delete, the user expects
the row they undid to look identical.

Idempotent: a second restore call with the same id is a no-op (returns
the id either way). If the id has been reused by a fresh create in the
meantime — extremely unlikely under UUIDs — we bail.
"""
import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  entity_existence_failure)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class RestoreStockItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    name: str = Field(min_length=1)
    stock_level_id: UUID
    stock_location_id: UUID | None = None
    stock_group_id: UUID | None = None
    expiry_date: date | None = None
    is_flagged: bool = False
    auto_add_when_low: bool = False
    is_open: bool = False


@dataclass(slots=True)
class RestoreStockItemResponse:
    stock_item_id: UUID | None = None
    already_exists: bool = False
    stock_level_not_found: bool = False


class RestoreStockItemHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, req: RestoreStockItemRequest) -> RestoreStockItemResponse:
        existing = self.repository.get(StockItem).by_id(req.stock_item_id)
        if existing is not None:
            # Idempotent: re-issuing the same restore call shouldn't error;
            # the row is already there.
            return RestoreStockItemResponse(
                stock_item_id=existing.id,
                already_exists=True,
            )

        level = self.repository.get(StockLevel).by_id(req.stock_level_id)
        if level is None:
            return RestoreStockItemResponse(stock_level_not_found=True)

        location: StockLocation | None = None
        if req.stock_location_id is not None:
            location = self.repository.get(StockLocation).by_id(req.stock_location_id)
            # Missing location is non-fatal — drop it (user can re-set).

        restored = StockItem(
            name=req.name,
            stock_level=level,
            stock_location=location,
            expiry_date=req.expiry_date,
            is_flagged=req.is_flagged,
            auto_add_when_low=req.auto_add_when_low,
            is_open=req.is_open,
        )
        # Force the original id so undo of a delete looks invisible.
        restored.id = req.stock_item_id
        if req.stock_group_id is not None:
            # The mapped column is on StockItem; set after construction
            # because the dataclass might not list it as a field.
            setattr(restored, "stock_group_id", req.stock_group_id)

        self.repository.add(restored)
        self.repository.save_changes()
        return RestoreStockItemResponse(stock_item_id=restored.id)


@STOCK_ITEM_ROUTER.route("/restore", methods=["POST"])
@has_request_body(RestoreStockItemRequest)
def restore_stock_item():
    _Logger = logging.getLogger(__name__)
    request: RestoreStockItemRequest = get_request_body()
    response = get_container().inject(RestoreStockItemHandler).handle(request)
    if response.stock_level_not_found:
        return entity_existence_failure("StockLevel", request.stock_level_id)
    if response.stock_item_id is None:
        return business_rule_violation("Could not restore stock item.")
    _Logger.info(
        "Restored stock item %s (already_exists=%s)",
        response.stock_item_id, response.already_exists,
    )
    return ok({
        "stock_item_id": str(response.stock_item_id),
        "already_exists": response.already_exists,
    })
