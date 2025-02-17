from varname import nameof

from application.dtos.stock_item_dto import StockItemDto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.update_stock_item.iupdate_stock_item_output_port import \
    IUpdateStockItemOutputPort
from domain.entities.base_entity import EntityID
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation
from framework.dora_api.infrastructure.base_presenter import BasePresenter


class UpdateStockItemPresenter(BasePresenter, IUpdateStockItemOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_stock_item_not_found_async(self, stock_item_id: EntityID):
        await self.not_found_async(nameof(StockItem), stock_item_id.value, 0)

    async def present_stock_level_not_found_async(self, stock_level_id: EntityID):
        await self.entity_existence_failure_async(nameof(StockLevel), nameof(stock_level_id), stock_level_id.value)

    async def present_stock_location_not_found_async(self, stock_location_id: EntityID):
        await self.entity_existence_failure_async(nameof(StockLocation), nameof(stock_location_id), stock_location_id.value)

    async def present_stock_item_updated_async(self, stock_item: StockItemDto):
        await self.persistence.save_changes_async()
        await self.no_content_async()
