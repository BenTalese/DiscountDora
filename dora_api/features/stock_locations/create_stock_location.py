import logging
from dataclasses import dataclass

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import STOCK_LOCATION_ROUTER
from dora_api.features.stock_locations.get_stock_locations import (
    StockLocationDto, get_stock_locations)
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import Field
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True, kw_only=True)
class CreateStockLocationRequest:
    name: str


@dataclass(slots=True)
class CreateStockLocationResponse:
    new_stock_location_id: EntityID = EntityID()
    stock_location_already_exists: bool = False


class CreateStockLocationHandler:

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateStockLocationRequest) -> CreateStockLocationResponse:
        _StockLocationName = Field(StockLocation, nameof(StockLocation.name))
        _ExistingStockLocation: StockLocation | None = (
            self.repository
            .get(StockLocation)
            .one(_StockLocationName.eq(request.name))
        )

        if _ExistingStockLocation:
            return CreateStockLocationResponse(stock_location_already_exists=True)

        _NewStockLocation = StockLocation(
            name = request.name
        )

        self.repository.add(_NewStockLocation)
        self.repository.save_changes()

        return CreateStockLocationResponse(new_stock_location_id=_NewStockLocation.id)


@STOCK_LOCATION_ROUTER.route("", methods=["POST"])
@has_request_body(CreateStockLocationRequest)
def create_stock_location():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to create stock location.")
    _Handler = get_container().inject(CreateStockLocationHandler)
    _Request: CreateStockLocationRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.stock_location_already_exists:
        _Logger.warning(f"Stock location already exists with name: {_Request.name}")
        return business_rule_violation(f"A stock location with the name '{_Request.name}' already exists.")

    _Logger.info(f"Successfully created stock location with ID: {_Response.new_stock_location_id.value}")
    return created(
        _Response.new_stock_location_id.value,
        f"{nameof(STOCK_LOCATION_ROUTER)}.{nameof(get_stock_locations)}",
        nameof(StockLocationDto.stock_location_id)
    )
