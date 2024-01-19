from application.dtos.stock_location_dto import StockLocationDto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_locations.create_stock_location.icreate_stock_location_output_port \
    import ICreateStockLocationOutputPort

from framework.api.infrastructure.base_presenter import BasePresenter
from framework.api.view_models.created_view_model import CreatedViewModel
from framework.api.view_models.stock_location_view_model import get_stock_location_view_model


class CreateStockLocationPresenter(BasePresenter, ICreateStockLocationOutputPort):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def present_stock_location_created_async(self, stock_location: StockLocationDto):
        await self.persistence_context.save_changes_async()
        await self.created_async(CreatedViewModel(stock_location.stock_location_id))
