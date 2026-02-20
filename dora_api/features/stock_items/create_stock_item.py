from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from flask import current_app
from varname import nameof

from application.infrastructure.bool_operation import Equal
from application.services.irepository import IRepository
from application.infrastructure.utils import get_request_body
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, created, entity_existence_failure, internal_server_error
from dora_api.infrastructure.dependency_container import DependencyContainer
from dora_api.infrastructure.decorators import has_request_body


@dataclass
class StockItemDto:
    name: str
    stock_item_id: UUID
    stock_level_id: UUID
    stock_location_id: UUID | None
    stock_level_last_updated: datetime


def to_dto(stock_item: StockItem) -> StockItemDto:
    return StockItemDto(
        name = stock_item.name,
        stock_item_id = stock_item.id.value,
        stock_level_id = stock_item.stock_level.id.value,
        stock_location_id = stock_item.stock_location.id.value if stock_item.stock_location else None,
        stock_level_last_updated = stock_item.stock_level_last_updated
    )


@dataclass(init=False, slots=True)
class CreateStockItemRequest:
    name: str
    stock_level_id: EntityID
    stock_location_id: EntityID | None = None


@dataclass(slots=True)
class CreateStockItemResponse:
    new_stock_item_id: UUID | None = None
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False
    stock_item_already_exists: bool = False


class CreateStockItemHandler:
    def __init__(
            self,
            stockItemRepository: IRepository[StockItem],
            stockLevelRepository: IRepository[StockLevel],
            stockLocationRepository: IRepository[StockLocation]):
        self.stockItemRepository = stockItemRepository
        self.stockLevelRepository = stockLevelRepository
        self.stockLocationRepository = stockLocationRepository

    def handle(self, request: CreateStockItemRequest) -> CreateStockItemResponse:
        _StockLevel = self.stockLevelRepository.get().first_by_id_or_none(request.stock_level_id)
        if not _StockLevel:
            return CreateStockItemResponse(stock_level_not_found = True)

        _StockLocation: StockLocation | None = None
        if request.stock_location_id:
            _StockLocation = self.stockLocationRepository.get().first_by_id_or_none(request.stock_location_id)

            if not _StockLocation:
                return CreateStockItemResponse(stock_location_not_found=True)

        _ExistingStockItem: StockItem | None = (
            self.stockItemRepository
            .get()
            .first_or_none(
                Equal((StockItem, nameof(StockItem.name)), request.name, is_case_insensitive = True))
        )

        if _ExistingStockItem:
            return CreateStockItemResponse(stock_item_already_exists=True)

        _NewStockItem = StockItem(
            days_until_stocktake_alert = 0,
            image = None,
            name = request.name,
            notes = None,
            stock_group = None,
            stock_level = _StockLevel,  # type: ignore
            stock_level_last_updated = datetime.now(),
            stock_location = _StockLocation,
            stocktake_alerts_are_enabled = False
        )

        self.stockItemRepository.add(_NewStockItem)
        self.stockItemRepository.save_changes()

        return CreateStockItemResponse(new_stock_item_id = _NewStockItem.id.value)


@STOCK_ITEM_ROUTER.route("", methods=["POST"])
@has_request_body(CreateStockItemRequest)
def create_stock_item():
    _Container: DependencyContainer = current_app.container  # type: ignore
    _Handler: CreateStockItemHandler = _Container.inject(CreateStockItemHandler)

    _Request: CreateStockItemRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.stock_level_not_found:
        return entity_existence_failure(nameof(StockLevel), nameof(CreateStockItemRequest.stock_level_id), _Request.stock_level_id.value)

    if _Response.stock_location_not_found and _Request.stock_location_id:
        return entity_existence_failure(nameof(StockLocation), nameof(CreateStockItemRequest.stock_location_id), _Request.stock_location_id.value)

    if _Response.stock_item_already_exists:
        return business_rule_violation(f"A stock item with the name '{_Request.name}' already exists.")

    if _Response.new_stock_item_id is None:
        return internal_server_error("An unknown error occurred while creating the stock item.")

    return created(_Response.new_stock_item_id, f"{nameof(STOCK_ITEM_ROUTER)}.{nameof(get_stock_items)}", nameof(StockItemDto.stock_item_id))
