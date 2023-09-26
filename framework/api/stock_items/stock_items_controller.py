from flask import Blueprint, current_app

from framework.api.stock_items.presenters import GetStockItemsPresenter
from interface_adaptors.controllers.stock_item_controller import StockItemController

stock_items = Blueprint("stock_items", __name__, url_prefix="/api/stockItems")

@stock_items.route("")
async def get_stock_items_async():
    stock_item_controller: StockItemController = current_app.stock_item_controller
    await stock_item_controller.get_stock_items_async(GetStockItemsPresenter())
