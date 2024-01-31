
from varname import nameof
from application.dtos.stock_item_dto import StockItemDto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.create_stock_item.icreate_stock_item_output_port import ICreateStockItemOutputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.view_models.created_view_model import CreatedViewModel


class CreateStockItemPresenter(BasePresenter, ICreateStockItemOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_stock_item_created_async(self, stock_item: StockItemDto):
        await self.persistence.save_changes_async()
        await self.created_async(CreatedViewModel(stock_item.stock_item_id.value))

    async def present_stock_level_not_found_async(self, stock_level_id: EntityID):
        await self.entity_existence_failure_async(nameof(stock_level_id), stock_level_id.value)

    async def present_stock_location_not_found_async(self, stock_location_id: EntityID):
        await self.entity_existence_failure_async(nameof(stock_location_id), stock_location_id.value)
