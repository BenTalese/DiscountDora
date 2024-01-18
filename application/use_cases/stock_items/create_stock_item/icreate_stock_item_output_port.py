from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_item_dto import StockItemDto
from domain.entities.base_entity import EntityID


class ICreateStockItemOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_item_created_async(self, stock_item: StockItemDto) -> None:
        pass

    @abstractmethod
    async def present_stock_level_not_found_async(self, stock_level_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_stock_location_not_found_async(self, stock_location_id: EntityID) -> None:
        pass
