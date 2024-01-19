from clapy import Interactor

from application.dtos.stock_item_dto import get_stock_item_dto
from application.services.ipersistence_context import IPersistenceContext
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation

from .create_stock_item_input_port import CreateStockItemInputPort
from .icreate_stock_item_output_port import ICreateStockItemOutputPort


class CreateStockItemInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: CreateStockItemInputPort, output_port: ICreateStockItemOutputPort):
        stock_item = StockItem(
            name = input_port.name,
            stock_level = self.persistence_context.get_entities(StockLevel).first_by_id(input_port.stock_level_id),
            stock_location = self.persistence_context.get_entities(StockLocation).first_by_id(input_port.stock_location_id)
                if input_port.stock_location_id else None
        )

        self.persistence_context.add(stock_item)

        await output_port.present_stock_item_created_async(get_stock_item_dto(stock_item))
