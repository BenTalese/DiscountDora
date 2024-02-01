from varname import nameof
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.delete_stock_item.idelete_stock_item_output_port import IDeleteStockItemOutputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.base_presenter import BasePresenter


class DeleteStockItemPresenter(BasePresenter, IDeleteStockItemOutputPort):

    def __init__(self, persistence: IPersistenceContext):
        self.persistence = persistence

    async def present_stock_item_deleted_async(self):
        await self.persistence.save_changes_async()
        await self.no_content_async()

    async def present_stock_item_not_found_async(self, stock_item_id: EntityID):
        await self.entity_existence_failure_async(nameof(stock_item_id), stock_item_id.value)
