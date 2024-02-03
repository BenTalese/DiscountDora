from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_location_dto import StockLocationDto
from application.services.iquerybuilder import IQueryBuilder


class IGetStockLocationsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_locations_async(self, stock_locations: IQueryBuilder[StockLocationDto]) -> None:
        pass
