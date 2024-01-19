from application.dtos.stock_item_dto import StockItemDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort
from framework.api.infrastructure.base_presenter import BasePresenter
from framework.api.view_models.stock_item_view_model import \
    get_stock_item_view_model

# TODO: Filtering has to be done like:
# 1. Send query string in
# 2. Pull apart query string using request.args.get (or whatever it is)
# 3. Give query to presenter
# 4. In presenter do "if i have a query, append that, then project and execute"
# ...
# Alternatively, just execute regardless and use an "after request" middleware to filter the already executed result

class GetStockItemsPresenter(BasePresenter, IGetStockItemsOutputPort):
    async def present_stock_items_async(self, stock_items: IQueryBuilder[StockItemDto]):
        await self.ok_async(stock_items.project(get_stock_item_view_model).execute())
