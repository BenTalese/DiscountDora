import logging
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.features.stock_items.get_stock_items import get_stock_items
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created,
                                                  entity_existence_failure)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateStockItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length = 1)
    stock_level_id: UUID
    stock_location_id: UUID | None = None
    stock_group_id: UUID | None = None
    expiry_date: date | None = None
    is_flagged: bool = False
    auto_add_when_low: bool = False
    is_open: bool = False
    # C-1 Chunk 6 / FU-033 — optional image as a data-URL string
    # ("data:image/...;base64,..."). Stored as UTF-8 bytes on the
    # entity; served back via GET /stock-items/<id>/image. Cap matches
    # the recipe-image cap (~4 MB raw → ~6 MB encoded).
    image: str | None = Field(default = None, max_length = 6_000_000)


@dataclass(slots=True)
class CreateStockItemResponse:
    new_stock_item_id: UUID = EMPTY_UUID
    stock_level_not_found: bool = False
    stock_location_not_found: bool = False
    stock_group_not_found: bool = False
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

        # Stock group is optional; we look it up locally so we can pass the
        # entity into the StockItem constructor (saves an extra round-trip
        # from the repository on read later).
        from dora_api.domain.entities.stock_group import StockGroup
        _StockGroup = None
        if request.stock_group_id:
            _StockGroup = self.repository.get(StockGroup).by_id(request.stock_group_id)
            if not _StockGroup:
                return CreateStockItemResponse(stock_group_not_found=True)

        _StockItemName = EntityField(StockItem, StockItem.Fields.NAME)
        _ExistingStockItem: StockItem | None = (
            self.repository
            .get(StockItem)
            .one(_StockItemName.eq(request.name))
        )

        if _ExistingStockItem:
            return CreateStockItemResponse(stock_item_already_exists=True)

        _NewStockItem = StockItem(
            days_until_stocktake_alert = 0,
            image = request.image.encode("utf-8") if request.image else None,
            name = request.name,
            notes = None,
            stock_group = _StockGroup,
            stock_level = _StockLevel,
            stock_level_last_updated = datetime.now(),
            stock_location = _StockLocation,
            stocktake_alerts_are_enabled = False,
            expiry_date = request.expiry_date,
            is_flagged = request.is_flagged,
            auto_add_when_low = request.auto_add_when_low,
            is_open = request.is_open,
            opened_on = date.today() if request.is_open else None,
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
        _Logger.warning(f"Stock level not found: {_Request.stock_level_id}")
        return entity_existence_failure(StockLevel.__name__, field_of(CreateStockItemRequest, 'stock_level_id'), _Request.stock_level_id)

    if _Response.stock_location_not_found and _Request.stock_location_id:
        _Logger.warning(f"Stock location not found: {_Request.stock_location_id}")
        return entity_existence_failure(StockLocation.__name__, field_of(CreateStockItemRequest, 'stock_location_id'), _Request.stock_location_id)

    if _Response.stock_group_not_found and _Request.stock_group_id:
        _Logger.warning(f"Stock group not found: {_Request.stock_group_id}")
        # Lazy import — avoids dragging StockGroup into the module's top-
        # level imports just for an error response constant.
        from dora_api.domain.entities.stock_group import StockGroup
        return entity_existence_failure(
            StockGroup.__name__,
            field_of(CreateStockItemRequest, 'stock_group_id'),
            _Request.stock_group_id,
        )

    if _Response.stock_item_already_exists:
        _Logger.warning(f"Stock item already exists with name: {_Request.name}")
        return business_rule_violation(f"A stock item with the name '{_Request.name}' already exists.")

    _Logger.info(f"Successfully created stock item with ID: {_Response.new_stock_item_id}")
    from dora_api.features.stock_items.get_stock_items import GetStockItemsHandler
    _Dto = get_container().inject(GetStockItemsHandler).handle_by_id(
        _Response.new_stock_item_id
    )
    return created(
        _Response.new_stock_item_id,
        f"{STOCK_ITEM_ROUTER.name}.{get_stock_items.__name__}",
        "stock_item_id",
        body = _Dto,
    )
