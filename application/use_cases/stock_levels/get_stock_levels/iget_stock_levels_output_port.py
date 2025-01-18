from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_level_dto import StockLevelDto
from application.services.iquerybuilder import IQueryBuilder


class IGetStockLevelsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_levels_async(self, stock_levels: IQueryBuilder[StockLevelDto]) -> None:
        pass
