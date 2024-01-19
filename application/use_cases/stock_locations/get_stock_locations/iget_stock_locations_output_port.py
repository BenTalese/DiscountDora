from abc import ABC, abstractmethod

from clapy import IOutputPort

from domain.entities.stock_location import StockLocation
from application.services.iquerybuilder import IQueryBuilder


class IGetStockLocationsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_locations_async(self, stock_locations: IQueryBuilder[StockLocation]) -> None:
        pass
    