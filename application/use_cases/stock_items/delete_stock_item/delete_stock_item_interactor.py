from clapy import Interactor

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.delete_stock_item.delete_stock_item_input_port import DeleteStockItemInputPort
from application.use_cases.stock_items.delete_stock_item.idelete_stock_item_output_port import IDeleteStockItemOutputPort
from domain.entities.stock_item import StockItem


class DeleteStockItemInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: DeleteStockItemInputPort, output_port: IDeleteStockItemOutputPort):
        _StockItem = self.persistence_context.get_entities(StockItem).first_by_id(input_port.stock_item_id)

        self.persistence_context.remove(_StockItem)

        await output_port.present_stock_item_deleted_async()
