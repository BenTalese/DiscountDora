from dataclasses import dataclass
import logging
from uuid import UUID

from varname import nameof

from dora_api.domain.entities.base_entity import EntityID
from dora_api.features.routers import STOCK_LOCATION_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, no_content, not_found
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.types import AttributeChangeTracker
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import Field
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class UpdateStockLocationRequest:
    name: AttributeChangeTracker[str] = AttributeChangeTracker[str]()


@dataclass(slots=True)
class UpdateStockLocationResponse:
    stock_location_already_exists: bool = False
    stock_location_not_found: bool = False


class UpdateStockLocationHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateStockLocationRequest, stock_location_id: EntityID) -> UpdateStockLocationResponse:
        # Get existing stock location
        _StockLocation: StockLocation | None = self.repository.get(StockLocation).by_id(stock_location_id)
        if not _StockLocation:
            return UpdateStockLocationResponse(stock_location_not_found=True)

        # Update name
        if request.name.has_been_set:
            _StockLocationName = Field(StockLocation, nameof(StockLocation.name))
            _SameNameStockLocation: StockLocation | None = (
                self.repository
                .get(StockLocation)
                .one(_StockLocationName.eq(request.name.value))
            )

            if _SameNameStockLocation and _SameNameStockLocation.id != stock_location_id:
                return UpdateStockLocationResponse(stock_location_already_exists=True)

            if request.name.value is not None:
                _StockLocation.name = request.name.value

        self.repository.save_changes()
        return UpdateStockLocationResponse()


@STOCK_LOCATION_ROUTER.route("<stock_location_id>", methods=["PATCH"])
@has_request_body(UpdateStockLocationRequest)
def update_stock_location(stock_location_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update stock location.")
    _Handler = get_container().inject(UpdateStockLocationHandler)
    _Request: UpdateStockLocationRequest = get_request_body()
    _Response = _Handler.handle(_Request, EntityID(stock_location_id))

    if _Response.stock_location_not_found:
        _Logger.warning(f"Stock location not found with ID: {stock_location_id}")
        return not_found(nameof(StockLocation), stock_location_id)

    if _Response.stock_location_already_exists:
        _Logger.warning(f"Stock location already exists with name: {_Request.name.value}")
        return business_rule_violation(f"A stock location with the name '{_Request.name.value}' already exists.")

    _Logger.info(f"Successfully updated stock location with ID: {stock_location_id}")
    return no_content()
