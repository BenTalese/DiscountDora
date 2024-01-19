from clapy import Interactor

from domain.entities.stock_location import StockLocation
from application.dtos.stock_location_dto import get_stock_location_dto
from application.services.ipersistence_context import IPersistenceContext

from .get_stock_locations_input_port import GetStockLocationsInputPort
from .iget_stock_locations_output_port import IGetStockLocationsOutputPort


class GetStockLocationsInteractor(Interactor):
    
    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetStockLocationsInputPort, output_port: IGetStockLocationsOutputPort) -> None:
        await output_port \
            .present_stock_locations_async(self.persistence_context
                                           .get_entities(StockLocation)
                                           .project(get_stock_location_dto))