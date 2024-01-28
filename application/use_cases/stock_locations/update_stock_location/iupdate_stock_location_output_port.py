from abc import ABC, abstractmethod

from clapy import IOutputPort

from domain.entities.base_entity import EntityID


# class IUpdateStockLocationOutputPort(ABC, IOutputPort):
#understand how it is figuring the inheritance ordering is wrong
class IUpdateStockLocationOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def stock_location_not_found_async(self, stock_location_id: EntityID):
        pass

    @abstractmethod
    async def stock_location_updated_async(self):
        pass
