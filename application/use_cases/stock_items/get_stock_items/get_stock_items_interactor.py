from clapy import Interactor
from varname import nameof
from application.dtos.stock_item_dto import get_stock_item_dto

from application.services.ipersistence_context import IPersistenceContext
from domain.entities.stock_item import StockItem

from .get_stock_items_input_port import GetStockItemsInputPort
from .iget_stock_items_output_port import IGetStockItemsOutputPort


class GetStockItemsInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetStockItemsInputPort, output_port: IGetStockItemsOutputPort):
        await output_port.present_stock_items_async(self.persistence_context.get_entities(StockItem).project(get_stock_item_dto))
