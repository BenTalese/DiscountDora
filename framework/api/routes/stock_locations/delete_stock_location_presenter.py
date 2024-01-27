from varname import nameof
from domain.entities.base_entity import EntityID
from application.use_cases.stock_locations.delete_stock_location.idelete_stock_location_output_port \
    import IDeleteStockLocationOutputPort
from framework.api.infrastructure.base_presenter import BasePresenter
from application.services.ipersistence_context import IPersistenceContext

class DeleteStockLocationPresenter(BasePresenter, IDeleteStockLocationOutputPort):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def stock_location_deleted_async(self, stock_location_id: EntityID):
        await self.persistence_context.save_changes_async()
        await self.no_content_async()

    async def stock_location_not_found_async(self, stock_location_id : EntityID):
        await self.entity_existence_failure_async(nameof(stock_location_id), stock_location_id.value)
