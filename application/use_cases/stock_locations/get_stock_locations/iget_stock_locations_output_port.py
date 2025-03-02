from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.services.iquerybuilder import IQueryBuilder
from domain.entities.stock_location import StockLocation


class IGetStockLocationsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_locations_async(self, stock_locations: IQueryBuilder[StockLocation]) -> None:
        pass
