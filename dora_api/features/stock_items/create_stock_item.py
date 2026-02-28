import logging
from dataclasses import dataclass
from datetime import datetime

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.features.stock_items.get_stock_items import (StockItemDto,
                                                           get_stock_items)
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created,
                                                  entity_existence_failure)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import Field
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True, kw_only=True)
class CreateStockItemRequest:
    name: str
    stock_level_id: EntityID
    stock_location_id: EntityID | None = None


@dataclass(slots=True)
class CreateStockItemResponse:
    new_stock_item_id: EntityID = EntityID()
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False
    stock_item_already_exists: bool = False


class CreateStockItemHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateStockItemRequest) -> CreateStockItemResponse:
        _StockLevel = self.repository.get(StockLevel).by_id(request.stock_level_id)
        if not _StockLevel:
            return CreateStockItemResponse(stock_level_not_found = True)

        _StockLocation: StockLocation | None = None
        if request.stock_location_id:
            _StockLocation = self.repository.get(StockLocation).by_id(request.stock_location_id)

            if not _StockLocation:
                return CreateStockItemResponse(stock_location_not_found=True)

        _StockItemName = Field(StockItem, nameof(StockItem.name))
        _ExistingStockItem: StockItem | None = (
            self.repository
            .get(StockItem)
            .one(_StockItemName.eq(request.name))
        )

        if _ExistingStockItem:
            return CreateStockItemResponse(stock_item_already_exists=True)

        _NewStockItem = StockItem(
            days_until_stocktake_alert = 0,
            image = None,
            name = request.name,
            notes = None,
            stock_group = None,
            stock_level = _StockLevel,
            stock_level_last_updated = datetime.now(),
            stock_location = _StockLocation,
            stocktake_alerts_are_enabled = False
        )

        self.repository.add(_NewStockItem)
        self.repository.save_changes()

        return CreateStockItemResponse(new_stock_item_id = _NewStockItem.id)


@STOCK_ITEM_ROUTER.route("", methods=["POST"])
@has_request_body(CreateStockItemRequest)
def create_stock_item():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to create stock item.")
    _Handler = get_container().inject(CreateStockItemHandler)
    _Request: CreateStockItemRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.stock_level_not_found:
        _Logger.warning(f"Stock level not found: {_Request.stock_level_id.value}")
        return entity_existence_failure(nameof(StockLevel), nameof(CreateStockItemRequest.stock_level_id), _Request.stock_level_id.value)

    if _Response.stock_location_not_found and _Request.stock_location_id:
        _Logger.warning(f"Stock location not found: {_Request.stock_location_id.value}")
        return entity_existence_failure(nameof(StockLocation), nameof(CreateStockItemRequest.stock_location_id), _Request.stock_location_id.value)

    if _Response.stock_item_already_exists:
        _Logger.warning(f"Stock item already exists with name: {_Request.name}")
        return business_rule_violation(f"A stock item with the name '{_Request.name}' already exists.")

    _Logger.info(f"Successfully created stock item with ID: {_Response.new_stock_item_id.value}")
    return created(
        _Response.new_stock_item_id.value,
        f"{nameof(STOCK_ITEM_ROUTER)}.{nameof(get_stock_items)}",
        nameof(StockItemDto.stock_item_id)
    )
