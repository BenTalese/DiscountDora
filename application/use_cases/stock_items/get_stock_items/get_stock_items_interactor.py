from clapy import Interactor

from application.infrastructure.mapping.dto_mappings import get_stock_item_dto
from application.services.imapper import IMapper
from application.services.ipersistence_context import IPersistenceContext
from domain.entities.stock_item import StockItem

from .get_stock_items_input_port import GetStockItemsInputPort
from .iget_stock_items_output_port import IGetStockItemsOutputPort


class GetStockItemsInteractor(Interactor):

    def __init__(self, mapper: IMapper, persistence_context: IPersistenceContext):
        self.mapper = mapper
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetStockItemsInputPort, output_port: IGetStockItemsOutputPort):
        x = self.persistence_context.get_entities(StockItem).execute()
        await output_port.present_stock_items_async(
            self.mapper.project(self.persistence_context.get_entities(StockItem), get_stock_item_dto))
