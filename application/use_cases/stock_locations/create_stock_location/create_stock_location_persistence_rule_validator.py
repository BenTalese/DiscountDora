from clapy import PersistenceRuleValidator
from varname import nameof
from application.infrastructure.bool_operation import Equal
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port import CreateStockLocationInputPort
from application.use_cases.stock_locations.create_stock_location.icreate_stock_location_output_port import ICreateStockLocationOutputPort
from domain.entities.stock_location import StockLocation


class CreateStockLocationPersistenceRuleValidator(PersistenceRuleValidator):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: CreateStockLocationInputPort, output_port: ICreateStockLocationOutputPort):
        _StockLocation: StockLocation = self.persistence_context \
            .get_entities(StockLocation) \
            .first_or_none(
                Equal((StockLocation, nameof(StockLocation.name)), input_port.name, True)
            )

        if _StockLocation:
            self.has_failures = True
            await output_port.present_stock_location_already_exists_async(input_port.name)
