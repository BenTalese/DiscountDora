from clapy import PersistenceRuleValidator
from varname import nameof
from application.infrastructure.bool_operation import Equal
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.update_stock_item.iupdate_stock_item_output_port import IUpdateStockItemOutputPort
from application.use_cases.stock_items.update_stock_item.update_stock_item_input_port import UpdateStockItemInputPort
from domain.entities.stock_item import StockItem


class UpdateStockItemPersistenceRuleValidator(PersistenceRuleValidator):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: UpdateStockItemInputPort, output_port: IUpdateStockItemOutputPort):
        if input_port.name.has_been_set:
            _StockItem: StockItem = self.persistence_context \
                .get_entities(StockItem) \
                .first_or_none(
                    Equal((StockItem, nameof(StockItem.name)), input_port.name.value, is_case_insensitive = True)
                )

            if _StockItem:
                self.has_failures = True
                await output_port.present_stock_item_already_exists_async(input_port.name)
