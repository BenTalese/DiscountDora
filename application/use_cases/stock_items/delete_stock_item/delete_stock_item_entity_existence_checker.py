from clapy import EntityExistenceChecker

from application.services.ientity_existence_checker import IEntityExistenceChecker
from application.use_cases.stock_items.delete_stock_item.delete_stock_item_input_port import DeleteStockItemInputPort
from application.use_cases.stock_items.delete_stock_item.idelete_stock_item_output_port import IDeleteStockItemOutputPort
from domain.entities.stock_item import StockItem


class DeleteStockItemEntityExistenceChecker(EntityExistenceChecker):

    def __init__(self, existence_checker: IEntityExistenceChecker):
        self.existence_checker = existence_checker

    async def execute_async(self, input_port: DeleteStockItemInputPort, output_port: IDeleteStockItemOutputPort):
        if not self.existence_checker.does_entity_exist(StockItem, input_port.stock_item_id):
            self.has_failures = True
            await output_port.present_stock_item_not_found_async(input_port.stock_item_id)
