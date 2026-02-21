from dataclasses import dataclass
from datetime import datetime
import logging
from typing import List
from uuid import UUID

from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_response
from dora_api.infrastructure.utils import get_container
from dora_api.services.irepository import IRepository


@dataclass(frozen=True, slots=True)
class StockItemDto:
    name: str
    stock_item_id: UUID
    stock_level_id: UUID
    stock_location_id: UUID | None
    stock_level_last_updated: datetime

    @classmethod
    def from_entity(cls, stock_item: StockItem) -> 'StockItemDto':
        return StockItemDto(
            name = stock_item.name,
            stock_item_id = stock_item.id.value,
            stock_level_id = stock_item.stock_level.id.value,
            stock_location_id = stock_item.stock_location.id.value if stock_item.stock_location else None,
            stock_level_last_updated = stock_item.stock_level_last_updated
        )


class GetStockItemsHandler:
    def __init__(self, repository: IRepository[StockItem]):
        self.repository = repository

    def handle(self) -> List[StockItemDto]:
        return self.repository.get().project(StockItemDto.from_entity)


@STOCK_ITEM_ROUTER.route("")
@STOCK_ITEM_ROUTER.route("<query>")
@has_response(StockItemDto)
def get_stock_items(query: str | None = None):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to get stock items.")
    _Handler = get_container().inject(GetStockItemsHandler)
    _Result = _Handler.handle()
    _Logger.info(f"Successfully retrieved {len(_Result)} stock items.")
    return ok(_Result)
