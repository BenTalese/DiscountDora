from clapy import IServiceProvider
from flask import Blueprint, current_app

from framework.api.routes.stock_levels.get_stock_levels_presenter import \
    GetStockLevelsPresenter
from interface_adaptors.controllers.stock_level_controller import \
    StockLevelController

STOCK_LEVEL_ROUTER = Blueprint("STOCK_LEVEL_ROUTER", __name__, url_prefix="/api/stock-levels")


@STOCK_LEVEL_ROUTER.route("")
@STOCK_LEVEL_ROUTER.route("<query>")
async def get_stock_levels_async(query = None):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLevelController: StockLevelController = _ServiceProvider.get_service(StockLevelController)
    _Presenter = GetStockLevelsPresenter()

    await _StockLevelController.get_stock_levels_async(_Presenter)
    return _Presenter.result
