from clapy import Interactor

from .delete_stock_location_input_port import DeleteStockLocationInputPort
from .idelete_stock_location_output_port import IDeleteStockLocationOutputPort

from domain.entities.stock_location import StockLocation
from application.services.ipersistence_context import IPersistenceContext


class DeleteStockLocationInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: DeleteStockLocationInputPort, output_port: IDeleteStockLocationOutputPort):
        _StockLocation = self.persistence_context \
            .get_entities(StockLocation) \
            .first_by_id(input_port.stock_location_id)

        self.persistence_context.remove(_StockLocation)

        await output_port.stock_location_deleted_async(input_port.stock_location_id)
