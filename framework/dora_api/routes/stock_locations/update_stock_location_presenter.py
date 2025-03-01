from varname import nameof

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_locations.update_stock_location.iupdate_stock_location_output_port import \
    IUpdateStockLocationOutputPort
from domain.entities.base_entity import EntityID
from domain.entities.stock_location import StockLocation
from framework.dora_api.infrastructure.base_presenter import BasePresenter


class UpdateStockLocationPresenter(BasePresenter, IUpdateStockLocationOutputPort):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def present_stock_location_already_exists_async(self, stock_location_name: str):
        await self.business_rule_violation_async(f"A stock location with the name '{stock_location_name}' already exists.")

    async def present_stock_location_not_found_async(self, stock_location_id: EntityID):
        await self.not_found_async(nameof(StockLocation), stock_location_id.value, 0)

    async def present_stock_location_updated_async(self):
        await self.persistence_context.save_changes_async()
        await self.no_content_async()
