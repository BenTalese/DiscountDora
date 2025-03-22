from varname import nameof

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.create_stock_item.icreate_stock_item_output_port import \
    ICreateStockItemOutputPort
from domain.entities.base_entity import EntityID
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.routes.stock_items.create_stock_item_command import \
    CreateStockItemCommand
from framework.dora_api.view_models.created_view_model import CreatedViewModel


class CreateStockItemPresenter(BasePresenter, ICreateStockItemOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_stock_item_already_exists_async(self, stock_item_name: str):
        self.request_body: CreateStockItemCommand
        await self.business_rule_violation_async(
            nameof(self.request_body.name),
            f"A stock item with the name '{stock_item_name}' already exists.")

    async def present_stock_item_created_async(self, stock_item: StockItem):
        await self.persistence.save_changes_async()
        await self.created_async(CreatedViewModel(stock_item.id.value), "stock_item_id")

    async def present_stock_level_not_found_async(self, stock_level_id: EntityID):
        await self.entity_existence_failure_async(nameof(StockLevel), nameof(stock_level_id), stock_level_id.value)

    async def present_stock_location_not_found_async(self, stock_location_id: EntityID):
        await self.entity_existence_failure_async(nameof(StockLocation), nameof(stock_location_id), stock_location_id.value)
