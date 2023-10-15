from clapy import IServiceProvider
from flask import current_app, jsonify
from application.dtos.stock_item_dto import StockItemDto
from application.services.iquerybuilder import IQueryBuilder

from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort
from framework.api.stock_items.view_models import get_stock_item_view_model


class GetStockItemsPresenter(IGetStockItemsOutputPort):
    async def present_stock_items_async(self, stock_items: IQueryBuilder[StockItemDto]):
        service_provider: IServiceProvider = current_app.service_provider
        # return mapper.project(stock_items(), get_stock_item_view_model)
        result = stock_items.project(get_stock_item_view_model).execute()
        x = jsonify(result)
        return jsonify(result)
