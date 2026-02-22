from dataclasses import dataclass
import logging
from typing import List
from uuid import UUID

from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.routers import STOCK_LOCATION_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.utils import get_container
from dora_api.services.irepository import IRepository


@dataclass(frozen=True, slots=True)
class StockLocationDto:
    name: str
    stock_location_id: UUID

    @classmethod
    def from_entity(cls, stock_location: StockLocation) -> 'StockLocationDto':
        return StockLocationDto(
            name = stock_location.name,
            stock_location_id = stock_location.id.value
        )


class GetStockLocationsHandler:
    def __init__(self, repository: IRepository[StockLocation]):
        self.repository = repository

    def handle(self) -> List[StockLocationDto]:
        return self.repository.get().project(StockLocationDto.from_entity)


@STOCK_LOCATION_ROUTER.route("")
@STOCK_LOCATION_ROUTER.route("<query>")
@has_response(StockLocationDto)
def get_stock_locations(query: str | None = None):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to get stock locations.")
    _Handler = get_container().inject(GetStockLocationsHandler)
    _Result = _Handler.handle()
    _Logger.info(f"Successfully retrieved {len(_Result)} stock locations.")
    return ok(_Result)
