from clapy import EntityExistenceChecker
from clapy.outputs import IOutputPort

from application.services.ientity_existence_checker import \
    IEntityExistenceChecker
from domain.entities.stock_location import StockLocation

from .iupdate_stock_location_output_port import IUpdateStockLocationOutputPort
from .update_stock_location_input_port import UpdateStockLocationInputPort


class UpdateStockLocationEntityExistenceChecker(EntityExistenceChecker):

    def __init__(self, entity_existence_checker: IEntityExistenceChecker):
        self.entity_existence_checker = entity_existence_checker

    async def execute_async(self, input_port: UpdateStockLocationInputPort, output_port: IUpdateStockLocationOutputPort) -> None:
        if not self.entity_existence_checker.does_entity_exist(StockLocation, input_port.stock_location_id):
            self.has_failures = True
            await output_port.stock_location_not_found_async(input_port.stock_location_id)
