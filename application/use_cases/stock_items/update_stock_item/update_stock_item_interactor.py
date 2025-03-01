from datetime import datetime
from clapy import Interactor

from application.dtos.stock_item_dto import get_stock_item_dto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.update_stock_item.iupdate_stock_item_output_port import \
    IUpdateStockItemOutputPort
from application.use_cases.stock_items.update_stock_item.update_stock_item_input_port import \
    UpdateStockItemInputPort
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation


class UpdateStockItemInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: UpdateStockItemInputPort, output_port: IUpdateStockItemOutputPort):
        _StockItem: StockItem = self.persistence_context \
            .get_entities(StockItem) \
            .first_by_id(input_port.stock_item_id)

        if input_port.name.has_been_set:
            _StockItem.name = input_port.name.value

        if input_port.stock_level_id.has_been_set:
            _StockItem.stock_level = self.persistence_context \
                .get_entities(StockLevel) \
                .first_by_id(input_port.stock_level_id.value)

            _StockItem.stock_level_last_updated = datetime.utcnow()

        if input_port.stock_location_id.has_been_set:
            _StockItem.stock_location = self.persistence_context \
                .get_entities(StockLocation) \
                .first_by_id(input_port.stock_location_id.value)

        self.persistence_context.update(_StockItem)
        await output_port.present_stock_item_updated_async(get_stock_item_dto(_StockItem))
