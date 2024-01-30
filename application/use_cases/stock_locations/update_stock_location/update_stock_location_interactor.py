from clapy import Interactor

from application.services.ipersistence_context import IPersistenceContext
from domain.entities.stock_location import StockLocation

from .iupdate_stock_location_output_port import IUpdateStockLocationOutputPort
from .update_stock_location_input_port import UpdateStockLocationInputPort


class UpdateStockLocationInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: UpdateStockLocationInputPort, output_port: IUpdateStockLocationOutputPort):
        _StockLocation: StockLocation = self.persistence_context \
            .get_entities(StockLocation) \
            .first_by_id(input_port.stock_location_id)

        if input_port.description.has_been_set:
            _StockLocation.description = input_port.description.value

        self.persistence_context.update(_StockLocation)

        #dto, do we send out dtos usually? is there a benefit?
        await output_port.stock_location_updated_async()
