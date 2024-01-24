from application.use_cases.stock_locations.update_stock_location.iupdate_stock_location_output_port import \
    IUpdateStockLocationOutputPort
from framework.api.infrastructure.base_presenter import BasePresenter
from domain.entities.base_entity import EntityID
from varname import nameof
from application.services.ipersistence_context import IPersistenceContext 

class UpdateStockLocationPresenter(BasePresenter, IUpdateStockLocationOutputPort):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def stock_location_not_found_async(self, stock_location_id: EntityID):
        self.entity_existence_failure_async(nameof(stock_location_id), stock_location_id)

    async def stock_location_updated_async(self):
        await self.persistence_context.save_changes_async
        await self.no_content_async
