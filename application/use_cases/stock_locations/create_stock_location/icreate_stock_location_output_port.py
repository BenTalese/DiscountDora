from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_location_dto import StockLocationDto


class ICreateStockLocationOutputPort(IOutputPort, ABC):
    
    @abstractmethod
    async def present_stock_location_created_async(self, stock_location: StockLocationDto) -> None:
        pass