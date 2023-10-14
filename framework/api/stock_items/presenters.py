from clapy import IServiceProvider
from flask import current_app, jsonify

from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort
from framework.api.stock_items.view_models import get_stock_item_view_model


class GetStockItemsPresenter(IGetStockItemsOutputPort):
    async def present_stock_items_async(self, stock_items): #TODO: Type hint here, and on output port
        service_provider: IServiceProvider = current_app.service_provider
        # return mapper.project(stock_items(), get_stock_item_view_model)
        return jsonify([get_stock_item_view_model(stock_item) for stock_item in stock_items()])
