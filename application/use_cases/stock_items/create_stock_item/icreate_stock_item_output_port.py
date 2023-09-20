from abc import ABC, abstractmethod

from clapy import IOutputPort

from application.dtos.stock_item_dto import StockItemDto


class ICreateStockItemOutputPort(IOutputPort, ABC):

    @abstractmethod
    async def present_stock_item_created_async(self, stock_item: StockItemDto) -> None:
        pass
