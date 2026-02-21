from clapy import PersistenceRuleValidator
from domain.entities.stock_location import StockLocation
from varname import nameof

from application.services.irepository import IPersistenceContext
from application.use_cases.stock_locations.update_stock_location.iupdate_stock_location_output_port import \
    IUpdateStockLocationOutputPort
from application.use_cases.stock_locations.update_stock_location.update_stock_location_input_port import \
    UpdateStockLocationInputPort
from dora_api.infrastructure.bool_operation import Equal


class UpdateStockLocationPersistenceRuleValidator(PersistenceRuleValidator):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: UpdateStockLocationInputPort, output_port: IUpdateStockLocationOutputPort):
        if input_port.name.has_been_set:
            _StockLocation: StockLocation = self.persistence_context \
                .get_entities(StockLocation) \
                .first_or_none(
                    Equal((StockLocation, nameof(StockLocation.name)), input_port.name.value, is_case_insensitive = True)
                )

            if _StockLocation:
                self.has_failures = True
                await output_port.present_stock_location_already_exists_async(input_port.name.value)
