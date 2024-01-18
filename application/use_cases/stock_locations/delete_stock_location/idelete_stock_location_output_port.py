from abc import ABC, abstractmethod

from clapy import IOutputPort

from domain.entities.base_entity import EntityID

class IDeleteStockLocationOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def stock_location_deleted_async(self, stock_location_id: EntityID) -> None: # Do i want to send out the ID?
        pass

    @abstractmethod
    async def stock_location_not_found_async(self, stock_location_id : EntityID) -> None:
        pass

# We should do the create response right from the start, i think it was created id in the header of the response?
    
# Should we include a version in the routes for extensibility, e.g., api/v1/stock
    