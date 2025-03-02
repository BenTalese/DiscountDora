from clapy import EntityExistenceChecker

from application.services.ientity_existence_checker import \
    IEntityExistenceChecker
from application.use_cases.stock_items.update_stock_item.iupdate_stock_item_output_port import \
    IUpdateStockItemOutputPort
from application.use_cases.stock_items.update_stock_item.update_stock_item_input_port import \
    UpdateStockItemInputPort
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


class UpdateStockItemEntityExistenceChecker(EntityExistenceChecker):

    def __init__(self, existence_checker: IEntityExistenceChecker):
        self.existence_checker = existence_checker

    async def execute_async(self, input_port: UpdateStockItemInputPort, output_port: IUpdateStockItemOutputPort):
        if not self.existence_checker.does_entity_exist(StockItem, input_port.stock_item_id):
            self.has_failures = True
            await output_port.present_stock_item_not_found_async(input_port.stock_item_id)

        if (input_port.stock_level_id.has_been_set
                and not self.existence_checker.does_entity_exist(StockLevel, input_port.stock_level_id.value)):
            self.has_failures = True
            await output_port.present_stock_level_not_found_async(input_port.stock_level_id.value)

        if (input_port.stock_location_id.has_been_set
                and not self.existence_checker.does_entity_exist(StockLocation, input_port.stock_location_id.value)):
            self.has_failures = True
            await output_port.present_stock_location_not_found_async(input_port.stock_location_id.value)
