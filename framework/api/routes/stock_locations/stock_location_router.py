from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof

from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port \
    import CreateStockLocationInputPort

from framework.api.routes.stock_locations.create_stock_location_command \
    import CreateStockLocationCommand
from framework.api.routes.stock_locations.create_stock_location_presenter \
    import CreateStockLocationPresenter
from framework.api.infrastructure.request_object_decorator import request_object

from interface_adaptors.controllers.stock_location_controller import \
    StockLocationController


STOCK_LOCATION_ROUTER = Blueprint("STOCK_LOCATION_ROUTER", __name__,  url_prefix="/api/stock-locations")
# /api/stocklocations, first slash necessary?

STOCK_LOCATION_ROUTER.root_path #test if how __name__ is working

@STOCK_LOCATION_ROUTER.route("", methods=["POST"])
@request_object('create_stock_location_async', CreateStockLocationCommand)
async def create_stock_location_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter = _ServiceProvider.get_service(CreateStockLocationPresenter)

    # _Presenter.get_route = f"{nameof(STOCK_LOCATION_ROUTER)}.{nameof(get_products_async)}"
    _Command: CreateStockLocationCommand = request.request_object
    _InputPort = CreateStockLocationInputPort(
        description = _Command.description
    )

    await _StockLocationController.create_stock_location_async(_InputPort, _Presenter)
    return _Presenter.result
