from varname import nameof

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.update_stock_item.iupdate_stock_item_output_port import \
    IUpdateStockItemOutputPort
from domain.entities.base_entity import EntityID
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.routes.stock_items.update_stock_item_command import \
    UpdateStockItemCommand


class UpdateStockItemPresenter(BasePresenter, IUpdateStockItemOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_stock_item_already_exists_async(self, stock_item_name: str):
        self.request_body: UpdateStockItemCommand
        await self.business_rule_violation_async(
            nameof(self.request_body.name),
            f"A stock item with the name '{stock_item_name}' already exists.")

    async def present_stock_item_not_found_async(self, stock_item_id: EntityID):
        await self.not_found_async(nameof(StockItem), stock_item_id.value, 0)

    async def present_stock_level_not_found_async(self, stock_level_id: EntityID):
        await self.entity_existence_failure_async(nameof(StockLevel), nameof(stock_level_id), stock_level_id.value)

    async def present_stock_location_not_found_async(self, stock_location_id: EntityID):
        await self.entity_existence_failure_async(nameof(StockLocation), nameof(stock_location_id), stock_location_id.value)

    async def present_stock_item_updated_async(self, stock_item: StockItem):
        await self.persistence.save_changes_async()
        await self.no_content_async()
