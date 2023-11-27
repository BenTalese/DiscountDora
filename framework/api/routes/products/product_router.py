from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof

from application.use_cases.products.create_product.create_product_input_port import \
    CreateProductInputPort
from domain.entities.base_entity import EntityID
from framework.api.routes.products.create_product_command import \
    CreateProductCommand
from framework.api.routes.products.create_product_presenter import \
    CreateProductPresenter
from interface_adaptors.controllers.product_controller import ProductController

PRODUCT_ROUTER = Blueprint("product_router", __name__, url_prefix="/api/products")

@PRODUCT_ROUTER.route("", methods=["POST"])
async def create_product_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _Presenter: CreateProductPresenter = _ServiceProvider.get_service(CreateProductPresenter)

    _Presenter.get_route = f"{nameof(PRODUCT_ROUTER)}.{nameof(get_products_async)}"
    _Command: CreateProductCommand = request.request_object
    _InputPort = CreateProductInputPort(
        brand = _Command.brand,
        image = _Command.image,
        is_available = _Command.is_available,
        merchant_id = EntityID(_Command.merchant_id),
        merchant_stockcode = _Command.merchant_stockcode,
        name = _Command.name,
        price_now = _Command.price_now,
        price_was = _Command.price_was,
        size_unit = _Command.size_unit,
        size_value = _Command.size_value,
        web_url = _Command.web_url)

    await _ProductController.create_product_async(_InputPort, _Presenter)
    return _Presenter.result


@PRODUCT_ROUTER.route("")
@PRODUCT_ROUTER.route("<query>")
async def get_products_async(query = None):
    pass
    # service_provider: IServiceProvider = current_app.service_provider
    # stock_item_controller: StockItemController = service_provider.get_service(StockItemController)
    # presenter = GetStockItemsPresenter()

    # await stock_item_controller.get_stock_items_async(presenter)
    # return presenter.result