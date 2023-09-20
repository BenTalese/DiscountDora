from abc import ABC, abstractmethod
from typing import List

from clapy import IOutputPort

from application.dtos.stock_item_dto import StockItemDto


class IGetStockItemsOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_items(self, stock_items: List[StockItemDto]) -> None: # TODO: Wrong type for stock_items
        pass
