from abc import ABC, abstractmethod

from clapy import IOutputPort, IValidationOutputPort

from application.dtos.stock_location_dto import StockLocationDto


class ICreateStockLocationOutputPort(IOutputPort, IValidationOutputPort, ABC):

    @abstractmethod
    async def present_stock_location_already_exists_async(self, stock_location_name: str) -> None:
        pass

    @abstractmethod
    async def present_stock_location_created_async(self, stock_location: StockLocationDto) -> None:
        pass
