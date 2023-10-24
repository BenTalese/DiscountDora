from flask import Blueprint, current_app

from framework.api.routes.stock_items.get_stock_items_presenter import \
    GetStockItemsPresenter
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController

stock_items = Blueprint("stock_items", __name__, url_prefix="/api/stockItems")

# Filtering options:
# Here in controller action
# Pass to presenter
# Pass to base presenter
# Middleware after_app_request

@stock_items.route("")
@stock_items.route("<query>")
async def get_stock_items_async(query = None):
    stock_item_controller: StockItemController = current_app.stock_item_controller
    presenter = GetStockItemsPresenter()
    await stock_item_controller.get_stock_items_async(presenter)
    return presenter.result
