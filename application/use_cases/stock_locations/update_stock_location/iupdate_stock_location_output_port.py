from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort

from domain.entities.base_entity import EntityID
from domain.entities.stock_location import StockLocation


class IUpdateStockLocationOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_stock_location_already_exists_async(self, stock_location_name: str) -> None:
        pass

    @abstractmethod
    async def present_stock_location_not_found_async(self, stock_location_id: EntityID) -> None:
        pass

    @abstractmethod
    async def present_stock_location_updated_async(self, stock_location: StockLocation) -> None:
        pass
