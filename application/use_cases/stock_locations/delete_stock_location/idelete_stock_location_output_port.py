from abc import ABC, abstractmethod

from clapy import IOutputPort

from domain.entities.base_entity import EntityID

class IDeleteStockLocationOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def stock_location_deleted_async(self, stock_location_id: EntityID) -> None:
        pass

    @abstractmethod
    async def stock_location_not_found_async(self, stock_location_id : EntityID) -> None:
        pass
