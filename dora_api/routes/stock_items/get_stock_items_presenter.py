from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort
from domain.entities.stock_item import StockItem
from framework.dora_api.infrastructure.base_presenter import BasePresenter
from framework.dora_api.view_models.stock_item_view_model import \
    get_stock_item_view_model


class GetStockItemsPresenter(BasePresenter, IGetStockItemsOutputPort):
    async def present_stock_items_async(self, stock_items: IQueryBuilder[StockItem]):
        await self.ok_async(stock_items.project(get_stock_item_view_model).execute())
