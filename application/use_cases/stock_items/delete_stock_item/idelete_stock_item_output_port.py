from abc import ABC, abstractmethod

from clapy import IOutputPort

from domain.entities.base_entity import EntityID


class IDeleteStockItemOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_item_deleted_async(self) -> None:
        pass

    @abstractmethod
    async def present_stock_item_not_found_async(self, stock_level_id: EntityID) -> None:
        pass
