from clapy import EntityExistenceChecker

from application.services.ientity_existence_checker import IEntityExistenceChecker
from application.use_cases.stock_items.create_stock_item.create_stock_item_input_port import CreateStockItemInputPort
from application.use_cases.stock_items.create_stock_item.icreate_stock_item_output_port import ICreateStockItemOutputPort
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


class CreateStockItemEntityExistenceChecker(EntityExistenceChecker):

    def __init__(self, existence_checker: IEntityExistenceChecker):
        self.existence_checker = existence_checker

    async def execute_async(self, input_port: CreateStockItemInputPort, output_port: ICreateStockItemOutputPort):
        if not self.existence_checker.does_entity_exist(StockLevel, input_port.stock_level_id):
            self.has_failures = True
            await output_port.present_stock_level_not_found_async(input_port.stock_level_id)

        if (input_port.stock_location_id and
            not self.existence_checker.does_entity_exist(StockLocation, input_port.stock_location_id)):
            self.has_failures = True
            await output_port.present_stock_location_not_found_async(input_port.stock_location_id)
