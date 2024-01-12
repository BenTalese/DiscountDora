from clapy import IServiceProvider
from flask import Blueprint, current_app

from framework.api.routes.stock_items.get_stock_items_presenter import \
    GetStockItemsPresenter
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController

STOCK_ITEM_ROUTER = Blueprint("STOCK_ITEM_ROUTER", __name__, url_prefix="/api/stockItems")

# Filtering options:
# Here in controller action
# Pass to presenter
# Pass to base presenter
# Middleware after_app_request

@STOCK_ITEM_ROUTER.route("")
@STOCK_ITEM_ROUTER.route("<query>")
async def get_stock_items_async(query = None):
    service_provider: IServiceProvider = current_app.service_provider
    stock_item_controller: StockItemController = service_provider.get_service(StockItemController)
    presenter = GetStockItemsPresenter()

    await stock_item_controller.get_stock_items_async(presenter)
    return presenter.result
