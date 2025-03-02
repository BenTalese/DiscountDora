from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.services.iquerybuilder import IQueryBuilder
from domain.entities.stock_item import StockItem


class IGetStockItemsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_items_async(self, stock_items: IQueryBuilder[StockItem]) -> None:
        pass
