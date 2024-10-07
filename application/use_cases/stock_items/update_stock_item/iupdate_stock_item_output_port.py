from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_item_dto import StockItemDto
from domain.entities.base_entity import EntityID
from typing import List


class IUpdateStockItemOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_products_to_add_not_found_async(self, product_ids: List[EntityID]) -> None:
        pass

    @abstractmethod
    async def present_products_to_remove_not_found_async(self, product_ids: List[EntityID]) -> None:
        pass

    @abstractmethod
    async def present_stock_item_not_found_async(self, stock_item_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_stock_level_not_found_async(self, stock_level_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_stock_location_not_found_async(self, stock_location_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_stock_item_updated_async(self, stock_item: StockItemDto) -> None:
        pass
