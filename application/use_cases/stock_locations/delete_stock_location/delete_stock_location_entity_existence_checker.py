from clapy import EntityExistenceChecker

from domain.entities.stock_location import StockLocation

from application.services.ientity_existence_checker import IEntityExistenceChecker
from application.use_cases.stock_locations.delete_stock_location.delete_stock_location_input_port \
    import DeleteStockLocationInputPort
from application.use_cases.stock_locations.delete_stock_location.idelete_stock_location_output_port \
    import IDeleteStockLocationOutputPort

class DeleteStockLocationEntityExistenceChecker(EntityExistenceChecker):
    
    def __init__(self, entity_existence_checker: IEntityExistenceChecker):
        self.entity_existence_checker = entity_existence_checker

    async def execute_async(self, input_port: DeleteStockLocationInputPort, output_port: IDeleteStockLocationOutputPort):
        if not self.entity_existence_checker.does_entity_exist(StockLocation, input_port.stock_location_id):
            # self.has_failures = True
            # ^ is this dynamically defining this variable in this instance?
            
            return output_port.stock_location_not_found_async(input_port.stock_location_id)
            #^ do we need to await? nothing else async is going on