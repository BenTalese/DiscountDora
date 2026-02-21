
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from uuid import UUID

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.types import AttributeChangeTracker
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, entity_existence_failure, no_content, not_found
from dora_api.infrastructure.bool_operation import Equal
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.services.irepository import IRepository


@dataclass(init=False, slots=True)
class UpdateStockItemRequest:
    name: AttributeChangeTracker[str] = AttributeChangeTracker[str]()
    stock_level_id: AttributeChangeTracker[EntityID] = AttributeChangeTracker[EntityID]()
    stock_location_id: AttributeChangeTracker[EntityID] = AttributeChangeTracker[EntityID]()


@dataclass(slots=True)
class UpdateStockItemResponse:
    stock_item_already_exists: bool = False
    stock_item_not_found: bool = False
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False


class UpdateStockItemHandler:
    def __init__(
            self,
            stock_item_repository: IRepository[StockItem],
            stock_level_repository: IRepository[StockLevel],
            stock_location_repository: IRepository[StockLocation]):
        self.stock_item_repository = stock_item_repository
        self.stock_level_repository = stock_level_repository
        self.stock_location_repository = stock_location_repository

    def handle(self, request: UpdateStockItemRequest, stock_item_id: EntityID) -> UpdateStockItemResponse:
        # Get existing stock item
        _StockItem: StockItem | None = self.stock_item_repository.get().by_id(stock_item_id)
        if not _StockItem:
            return UpdateStockItemResponse(stock_item_not_found = True)

        # Update stock level
        if request.stock_level_id.has_been_set and request.stock_level_id.value is not None:
            _StockLevel = self.stock_level_repository.get().by_id(request.stock_level_id.value)

            if not _StockLevel:
                return UpdateStockItemResponse(stock_level_not_found=True)
            _StockItem.stock_level = _StockLevel
            _StockItem.stock_level_last_updated = datetime.now(UTC)

        # Update stock location
        _StockLocation: StockLocation | None = None
        if request.stock_location_id.has_been_set and request.stock_location_id.value is not None:
            _StockLocation = self.stock_location_repository.get().by_id(request.stock_location_id.value)

            if not _StockLocation:
                return UpdateStockItemResponse(stock_location_not_found=True)

        if request.stock_location_id.has_been_set:
            _StockItem.stock_location = _StockLocation

        # Update name
        if request.name.has_been_set:
            _SameNameStockItem: StockItem | None = (
                self.stock_item_repository
                .get()
                .one(Equal((StockItem, nameof(StockItem.name)), request.name.value, is_case_insensitive = True))
            )

            if _SameNameStockItem:
                return UpdateStockItemResponse(stock_item_already_exists=True)

        if request.name.has_been_set and request.name.value is not None:
            _StockItem.name = request.name.value

        self.stock_item_repository.update(_StockItem)
        self.stock_item_repository.save_changes()
        return UpdateStockItemResponse()


@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["PATCH"])
@has_request_body(UpdateStockItemRequest)
def update_stock_item(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update stock item.")
    _Handler = get_container().inject(UpdateStockItemHandler)
    _Request: UpdateStockItemRequest = get_request_body()
    _Response = _Handler.handle(_Request, EntityID(stock_item_id))

    if _Response.stock_item_not_found:
        _Logger.warning(f"Stock item not found with ID: {stock_item_id}")
        return not_found(nameof(StockItem), stock_item_id)

    if _Response.stock_item_already_exists:
        _Logger.warning(f"Stock item already exists with name: {_Request.name.value}")
        return business_rule_violation(f"A stock item with the name '{_Request.name}' already exists.")

    if _Response.stock_level_not_found and _Request.stock_level_id.value is not None:
        _Logger.warning(f"Stock level not found: {_Request.stock_level_id.value}")
        return entity_existence_failure(nameof(StockLevel), nameof(UpdateStockItemRequest.stock_level_id), _Request.stock_level_id.value.value)

    if _Response.stock_location_not_found and _Request.stock_location_id.value is not None:
        _Logger.warning(f"Stock location not found: {_Request.stock_location_id.value}")
        return entity_existence_failure(
            nameof(StockLocation),
            nameof(UpdateStockItemRequest.stock_location_id),
            _Request.stock_location_id.value.value)

    _Logger.info(f"Successfully updated stock item with ID: {stock_item_id}")
    return no_content()
