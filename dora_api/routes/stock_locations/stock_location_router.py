from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof

from application.use_cases.stock_locations.create_stock_location.create_stock_location_input_port import \
    CreateStockLocationInputPort
from application.use_cases.stock_locations.delete_stock_location.delete_stock_location_input_port import \
    DeleteStockLocationInputPort
from application.use_cases.stock_locations.update_stock_location.update_stock_location_input_port import \
    UpdateStockLocationInputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.command_mapper import get_input_port_from_command
from framework.dora_api.infrastructure.request_body_decorator import \
    has_request_body
from framework.dora_api.infrastructure.view_model_decorator import has_view_model
from framework.dora_api.routes.stock_locations.create_stock_location_command import \
    CreateStockLocationCommand
from framework.dora_api.routes.stock_locations.create_stock_location_presenter import \
    CreateStockLocationPresenter
from framework.dora_api.routes.stock_locations.delete_stock_location_presenter import \
    DeleteStockLocationPresenter
from framework.dora_api.routes.stock_locations.get_stock_locations_presenter import \
    GetStockLocationsPresenter
from framework.dora_api.routes.stock_locations.update_stock_location_command import \
    UpdateStockLocationCommand
from framework.dora_api.routes.stock_locations.update_stock_location_presenter import \
    UpdateStockLocationPresenter
from framework.dora_api.view_models.stock_location_view_model import StockLocationViewModel
from interface_adaptors.controllers.stock_location_controller import \
    StockLocationController






@STOCK_LOCATION_ROUTER.route("<stock_location_id>", methods=["DELETE"])
async def delete_stock_location_async(stock_location_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter: DeleteStockLocationPresenter = _ServiceProvider.get_service(DeleteStockLocationPresenter)

    _InputPort = DeleteStockLocationInputPort()
    _InputPort.stock_location_id = EntityID(stock_location_id)

    await _StockLocationController.delete_stock_location_async(_InputPort, _Presenter)
    return _Presenter.result


@STOCK_LOCATION_ROUTER.route("<stock_location_id>", methods=["PATCH"])
@has_request_body("update_stock_location_async", UpdateStockLocationCommand)
async def update_stock_location_async(stock_location_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockLocationController: StockLocationController = _ServiceProvider.get_service(StockLocationController)
    _Presenter: UpdateStockLocationPresenter = _ServiceProvider.get_service(UpdateStockLocationPresenter)

    _Command: UpdateStockLocationCommand = request.request_body
    _InputPort = get_input_port_from_command(_Command, UpdateStockLocationInputPort)
    _InputPort.stock_location_id = EntityID(stock_location_id)

    await _StockLocationController.update_stock_location_async(_InputPort, _Presenter)
    return _Presenter.result
