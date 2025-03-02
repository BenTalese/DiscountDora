from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.services.iquerybuilder import IQueryBuilder
from domain.entities.stock_level import StockLevel


class IGetStockLevelsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_levels_async(self, stock_levels: IQueryBuilder[StockLevel]) -> None:
        pass
