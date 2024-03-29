from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof

from application.use_cases.stock_items.create_stock_item.create_stock_item_input_port import \
    CreateStockItemInputPort
from application.use_cases.stock_items.delete_stock_item.delete_stock_item_input_port import \
    DeleteStockItemInputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.request_body_decorator import \
    has_request_body
from framework.dora_api.routes.stock_items.create_stock_item_command import \
    CreateStockItemCommand
from framework.dora_api.routes.stock_items.create_stock_item_presenter import \
    CreateStockItemPresenter
from framework.dora_api.routes.stock_items.delete_stock_item_presenter import \
    DeleteStockItemPresenter
from framework.dora_api.routes.stock_items.get_stock_items_presenter import \
    GetStockItemsPresenter
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController

STOCK_ITEM_ROUTER = Blueprint("STOCK_ITEM_ROUTER", __name__, url_prefix="/api/stock-items")

# TODO
# Filtering options:
# Here in controller action
# Pass to presenter
# Pass to base presenter
# Middleware after_app_request

@STOCK_ITEM_ROUTER.route("", methods=["POST"])
@has_request_body('create_stock_item_async', CreateStockItemCommand)
async def create_stock_item_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockItemController: StockItemController = _ServiceProvider.get_service(StockItemController)
    _Presenter: CreateStockItemPresenter = _ServiceProvider.get_service(CreateStockItemPresenter)

    _Presenter.get_route = f"{nameof(STOCK_ITEM_ROUTER)}.{nameof(get_stock_items_async)}"
    _Command: CreateStockItemCommand = request.request_body
    _InputPort = CreateStockItemInputPort()
    _InputPort.name = _Command.name
    if _Command.stock_level_id:
        _InputPort.stock_level_id = EntityID(_Command.stock_level_id)
    _InputPort.stock_location_id = EntityID(_Command.stock_location_id) if _Command.stock_location_id else None

    await _StockItemController.create_stock_item_async(_InputPort, _Presenter)
    return _Presenter.result

@STOCK_ITEM_ROUTER.route("<stock_item_id>", methods=["DELETE"])
async def delete_stock_item_async(stock_item_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockItemController: StockItemController = _ServiceProvider.get_service(StockItemController)
    _Presenter: DeleteStockItemPresenter = _ServiceProvider.get_service(DeleteStockItemPresenter)

    _InputPort = DeleteStockItemInputPort()
    _InputPort.stock_item_id = EntityID(stock_item_id)

    await _StockItemController.delete_stock_item_async(_InputPort, _Presenter)
    return _Presenter.result

@STOCK_ITEM_ROUTER.route("")
@STOCK_ITEM_ROUTER.route("<query>")
async def get_stock_items_async(query = None):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _StockItemController: StockItemController = _ServiceProvider.get_service(StockItemController)
    _Presenter = GetStockItemsPresenter()

    await _StockItemController.get_stock_items_async(_Presenter)
    return _Presenter.result
