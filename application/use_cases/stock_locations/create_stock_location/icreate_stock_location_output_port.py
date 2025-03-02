from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort

from domain.entities.stock_location import StockLocation


class ICreateStockLocationOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_stock_location_already_exists_async(self, stock_location_name: str) -> None:
        pass

    @abstractmethod
    async def present_stock_location_created_async(self, stock_location: StockLocation) -> None:
        pass
