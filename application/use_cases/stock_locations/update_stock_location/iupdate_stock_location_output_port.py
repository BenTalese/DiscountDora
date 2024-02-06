from abc import ABC, abstractmethod

from clapy import IOutputPort

from domain.entities.base_entity import EntityID


class IUpdateStockLocationOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_location_not_found_async(self, stock_location_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_stock_location_updated_async(self) -> None:
        pass
