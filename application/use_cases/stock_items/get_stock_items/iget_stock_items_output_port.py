from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_item_dto import StockItemDto
from application.services.iquerybuilder import IQueryBuilder


class IGetStockItemsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_items_async(self, stock_items: IQueryBuilder[StockItemDto]) -> None:
        pass
