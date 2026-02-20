from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof

from application.use_cases.stock_items.create_stock_item.create_stock_item_input_port import \
    CreateStockItemInputPort
from application.use_cases.stock_items.delete_stock_item.delete_stock_item_input_port import \
    DeleteStockItemInputPort
from application.use_cases.stock_items.update_stock_item.update_stock_item_input_port import \
    UpdateStockItemInputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.command_mapper import get_input_port_from_command
from framework.dora_api.infrastructure.request_body_decorator import \
    has_request_body
from framework.dora_api.infrastructure.view_model_decorator import \
    has_view_model
from framework.dora_api.routes.stock_items.create_stock_item_command import \
    CreateStockItemCommand
from framework.dora_api.routes.stock_items.create_stock_item_presenter import \
    CreateStockItemPresenter
from framework.dora_api.routes.stock_items.delete_stock_item_presenter import \
    DeleteStockItemPresenter
from framework.dora_api.routes.stock_items.get_stock_items_presenter import \
    GetStockItemsPresenter
from framework.dora_api.routes.stock_items.update_stock_item_command import \
    UpdateStockItemCommand
from framework.dora_api.routes.stock_items.update_stock_item_presenter import \
    UpdateStockItemPresenter
from framework.dora_api.view_models.stock_item_view_model import \
    StockItemViewModel
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController




@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["DELETE"])
async def delete_stock_item_async(stock_item_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockItemController: StockItemController = _ServiceProvider.get_service(StockItemController)
    _Presenter: DeleteStockItemPresenter = _ServiceProvider.get_service(DeleteStockItemPresenter)

    _InputPort = DeleteStockItemInputPort()
    _InputPort.stock_item_id = EntityID(stock_item_id)

    await _StockItemController.delete_stock_item_async(_InputPort, _Presenter)
    return _Presenter.result


@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["PATCH"])
@has_request_body('update_stock_item_async', UpdateStockItemCommand)
async def update_stock_item_async(stock_item_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockItemController: StockItemController = _ServiceProvider.get_service(StockItemController)
    _Presenter: UpdateStockItemPresenter = _ServiceProvider.get_service(UpdateStockItemPresenter)

    _Command: UpdateStockItemCommand = request.request_body
    _InputPort = get_input_port_from_command(_Command, UpdateStockItemInputPort)
    _InputPort.stock_item_id = EntityID(stock_item_id)

    await _StockItemController.update_stock_item_async(_InputPort, _Presenter)
    return _Presenter.result
