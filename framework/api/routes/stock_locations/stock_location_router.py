from clapy import IServiceProvider
from flask import Blueprint, current_app, request

from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port \
    import CreateStockLocationInputPort
from framework.api.routes.stock_locations.create_stock_location_command \
    import CreateStockLocationCommand
from framework.api.routes.stock_locations.create_stock_location_presenter \
    import CreateStockLocationPresenter
from interface_adaptors.controllers.stock_location import \
    StockLocationController


STOCK_LOCATION_ROUTER = Blueprint("stock-location-router", __name__,  url_prefix="/api/stock-locations")
# /api/stocklocations, first slash necessary?

STOCK_LOCATION_ROUTER.root_path #test if how __name__ is working

@STOCK_LOCATION_ROUTER.route("", methods=["POST"])
async def create_stock_location_async():
    _Service_provider: IServiceProvider = current_app.service_provider
    _Stock_location_controller: StockLocationController = _Service_provider.get_service(StockLocationController)
    _Presenter = CreateStockLocationPresenter()

    # _Presenter.get_route = f"{nameof(PRODUCT_ROUTER)}.{nameof(get_products_async)}"
    _Command: CreateStockLocationCommand = request.request_object
    _Input_port: CreateStockLocationInputPort(
        description = _Command.description)

    await _Stock_location_controller.create_stock_location_async(_Input_port, _Presenter)
    return _Presenter.result
