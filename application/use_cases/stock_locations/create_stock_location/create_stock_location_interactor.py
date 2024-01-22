from clapy import Interactor

from .create_stock_location_input_port import CreateStockLocationInputPort
from .icreate_stock_location_output_port import ICreateStockLocationOutputPort

from domain.entities.stock_location import StockLocation

from application.dtos.stock_location_dto import get_stock_location_dto
from application.services.ipersistence_context import IPersistenceContext


class CreateStockLocationInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: CreateStockLocationInputPort, output_port: ICreateStockLocationOutputPort):
        stock_location = StockLocation( 
            description = input_port.description
        )

        self.persistence_context.add(stock_location)

        await output_port.present_stock_location_created_async(get_stock_location_dto(stock_location))
