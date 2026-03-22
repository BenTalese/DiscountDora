
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from varname import nameof

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.types import UNSET, Unset
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  entity_existence_failure,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (get_container, get_request_body,
                                           is_set)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateStockItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | Unset = Field(default = UNSET, min_length = 1)
    stock_level_id: UUID | Unset = UNSET
    stock_location_id: UUID | None | Unset = UNSET


@dataclass(slots=True)
class UpdateStockItemResponse:
    stock_item_already_exists: bool = False
    stock_item_not_found: bool = False
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False


class UpdateStockItemHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateStockItemRequest, stock_item_id: UUID) -> UpdateStockItemResponse:
        # Get existing stock item
        _StockItem: StockItem | None = self.repository.get(StockItem).by_id(stock_item_id)
        if not _StockItem:
            return UpdateStockItemResponse(stock_item_not_found = True)

        # Update stock level
        if is_set(request.stock_level_id):
            _StockLevel = self.repository.get(StockLevel).by_id(request.stock_level_id)

            if not _StockLevel:
                return UpdateStockItemResponse(stock_level_not_found=True)
            _StockItem.stock_level = _StockLevel
            _StockItem.stock_level_last_updated = datetime.now(UTC)

        # Update stock location
        _StockLocation: StockLocation | None = None
        if is_set(request.stock_location_id) and request.stock_location_id is not None:
            _StockLocation = self.repository.get(StockLocation).by_id(request.stock_location_id)

            if not _StockLocation:
                return UpdateStockItemResponse(stock_location_not_found=True)

        if is_set(request.stock_location_id):
            _StockItem.stock_location = _StockLocation

        # Update name
        if is_set(request.name):
            _StockItemName = EntityField(StockItem, nameof(StockItem.name))
            _SameNameStockItem: StockItem | None = (
                self.repository
                .get(StockItem)
                .one(_StockItemName.eq(request.name))
            )

            if _SameNameStockItem and _SameNameStockItem.id != stock_item_id:
                return UpdateStockItemResponse(stock_item_already_exists=True)

            _StockItem.name = request.name

        self.repository.save_changes()
        return UpdateStockItemResponse()


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
        return not_found(nameof(StockItem), stock_item_id)

    if _Response.stock_item_already_exists:
        _Logger.warning(f"Stock item already exists with name: {_Request.name}")
        return business_rule_violation(f"A stock item with the name '{_Request.name}' already exists.")

    if _Response.stock_level_not_found and is_set(_Request.stock_level_id):
        _Logger.warning(f"Stock level not found: {_Request.stock_level_id}")
        return entity_existence_failure(nameof(StockLevel), nameof(UpdateStockItemRequest.stock_level_id), _Request.stock_level_id)

    if (_Response.stock_location_not_found and is_set(_Request.stock_location_id) and _Request.stock_location_id is not None):
        _Logger.warning(f"Stock location not found: {_Request.stock_location_id}")
        return entity_existence_failure(nameof(StockLocation), nameof(UpdateStockItemRequest.stock_location_id), _Request.stock_location_id)

    _Logger.info(f"Successfully updated stock item with ID: {stock_item_id}")
    return no_content()
