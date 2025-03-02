from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort

from domain.entities.base_entity import EntityID
from domain.entities.stock_item import StockItem


class IUpdateStockItemOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_stock_item_already_exists_async(self, stock_item_name: str) -> None:
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
    async def present_stock_item_updated_async(self, stock_item: StockItem) -> None:
        pass
