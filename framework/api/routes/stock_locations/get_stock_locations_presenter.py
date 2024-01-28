from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.stock_locations.get_stock_locations.iget_stock_locations_output_port import \
    IGetStockLocationsOutputPort
from domain.entities.stock_location import StockLocation
from framework.api.infrastructure.base_presenter import BasePresenter
from framework.api.view_models.stock_location_view_model import \
    get_stock_location_view_model


class GetStockLocationsPresenter(BasePresenter, IGetStockLocationsOutputPort):

    async def present_stock_locations_async(self, stock_locations: IQueryBuilder[StockLocation]):
        await self.ok_async(stock_locations.project(get_stock_location_view_model).execute())
