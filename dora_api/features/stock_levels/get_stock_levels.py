import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import STOCK_LEVEL_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.utils import get_container
from dora_api.services.irepository import IRepository


@dataclass(frozen=True, slots=True)
class StockLevelDto:
    name: str
    sequence: int
    stock_level_id: UUID

    @classmethod
    def from_entity(cls, stock_level: StockLevel) -> 'StockLevelDto':
        return StockLevelDto(
            name = stock_level.name,
            sequence = stock_level.sequence,
            stock_level_id = stock_level.id.value
        )


class GetStockLevelsHandler:
    def __init__(self, repository: IRepository[StockLevel]):
        self.repository = repository

    def handle(self) -> List[StockLevelDto]:
        return self.repository.get().project(StockLevelDto.from_entity)


@STOCK_LEVEL_ROUTER.route("")
@STOCK_LEVEL_ROUTER.route("<query>")
@has_response(StockLevelDto)
def get_stock_levels(query: str | None = None):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to get stock levels.")
    _Handler = get_container().inject(GetStockLevelsHandler)
    _Result = _Handler.handle()
    _Logger.info(f"Successfully retrieved {len(_Result)} stock levels.")
    return ok(_Result)
