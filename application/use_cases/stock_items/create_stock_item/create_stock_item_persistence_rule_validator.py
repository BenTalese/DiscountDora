from clapy import PersistenceRuleValidator
from varname import nameof
from application.infrastructure.bool_operation import Equal
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.create_stock_item.create_stock_item_input_port import CreateStockItemInputPort
from application.use_cases.stock_items.create_stock_item.icreate_stock_item_output_port import ICreateStockItemOutputPort
from domain.entities.stock_item import StockItem


class CreateStockItemPersistenceRuleValidator(PersistenceRuleValidator):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: CreateStockItemInputPort, output_port: ICreateStockItemOutputPort):
        _StockItem: StockItem = self.persistence_context \
            .get_entities(StockItem) \
            .first_or_none(
                Equal((StockItem, nameof(StockItem.name)), input_port.name, True)
            )

        if _StockItem:
            self.has_failures = True
            await output_port.present_stock_item_already_exists_async(input_port.name)
