from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof
from domain.entities.base_entity import EntityID
from application.infrastructure.attribute_change_tracker import \
    AttributeChangeTracker
from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port import \
    CreateStockLocationInputPort
from application.use_cases.stock_locations.delete_stock_location.delete_stock_location_input_port import \
    DeleteStockLocationInputPort
from application.use_cases.stock_locations.update_stock_location.update_stock_location_input_port import \
    UpdateStockLocationInputPort
from framework.api.infrastructure.request_object_decorator import request_object
from framework.api.routes.stock_locations.create_stock_location_command import \
    CreateStockLocationCommand
from framework.api.routes.stock_locations.create_stock_location_presenter import \
    CreateStockLocationPresenter
from framework.api.routes.stock_locations.get_stock_locations_presenter import \
     GetStockLocationsPresenter
from framework.api.routes.stock_locations.delete_stock_location_presenter import \
    DeleteStockLocationPresenter
from framework.api.routes.stock_locations.update_stock_location_command import \
    UpdateStockLocationCommand
from framework.api.routes.stock_locations.update_stock_location_presenter import \
    UpdateStockLocationPresenter
from interface_adaptors.controllers.stock_location_controller import \
    StockLocationController


STOCK_LOCATION_ROUTER = Blueprint("STOCK_LOCATION_ROUTER", __name__,  url_prefix="/api/stock-locations")

@STOCK_LOCATION_ROUTER.route("", methods=["POST"])
@request_object('create_stock_location_async', CreateStockLocationCommand)
async def create_stock_location_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter: CreateStockLocationPresenter = _ServiceProvider.get_service(CreateStockLocationPresenter)
    _Presenter.get_route = f"{nameof(STOCK_LOCATION_ROUTER)}.{nameof(get_stock_locations_async)}"

    _Command: CreateStockLocationCommand = request.request_object
    _InputPort = CreateStockLocationInputPort(
        description = _Command.description
    )

    await _StockLocationController.create_stock_location_async(_InputPort, _Presenter)
    return _Presenter.result

@STOCK_LOCATION_ROUTER.route("/<stock_location_id>", methods=["DELETE"])
async def delete_stock_location_async(stock_location_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter: DeleteStockLocationPresenter = _ServiceProvider.get_service(DeleteStockLocationPresenter)

    _InputPort: DeleteStockLocationInputPort = DeleteStockLocationInputPort()
    _InputPort.stock_location_id = EntityID(stock_location_id)

    await _StockLocationController.delete_stock_location_async(_InputPort, _Presenter)
    return _Presenter.result

@STOCK_LOCATION_ROUTER.route("")
@STOCK_LOCATION_ROUTER.route("<query>")
async def get_stock_locations_async(query = None):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter = GetStockLocationsPresenter()

    await _StockLocationController.get_stock_locations_async(_Presenter)
    return _Presenter.result

@STOCK_LOCATION_ROUTER.route("", methods=["PATCH"])
@request_object("update_stock_location_async", DeleteStockLocationCommand)
async def update_stock_location_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter: UpdateStockLocationPresenter = _ServiceProvider.get_service(UpdateStockLocationPresenter)

    _Command: UpdateStockLocationCommand = current_app.request_object
    _InputPort: UpdateStockLocationInputPort = UpdateStockLocationInputPort(
        description = _Command.description,
        stock_location_id = _Command.stock_location_id
    )

    await _StockLocationController.update_stock_location_async(_InputPort, _Presenter)
    return _Presenter.result
