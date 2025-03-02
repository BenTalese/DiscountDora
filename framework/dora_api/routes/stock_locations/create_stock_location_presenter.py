from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_locations.create_stock_location.icreate_stock_location_output_port import \
    ICreateStockLocationOutputPort
from domain.entities.stock_location import StockLocation
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.view_models.created_view_model import CreatedViewModel


class CreateStockLocationPresenter(BasePresenter, ICreateStockLocationOutputPort):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def present_stock_location_already_exists_async(self, stock_location_name: str):
        await self.business_rule_violation_async(f"A stock location with the name '{stock_location_name}' already exists.")

    async def present_stock_location_created_async(self, stock_location: StockLocation):
        await self.persistence_context.save_changes_async()
        await self.created_async(CreatedViewModel(stock_location.id.value), "stock_location_id")
