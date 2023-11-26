from clapy import IServiceProvider
from flask import Blueprint, current_app, make_response, request
from application.use_cases.products.create_product.create_product_input_port import CreateProductInputPort
from framework.api.routes.products.create_product_presenter import CreateProductPresenter

from interface_adaptors.controllers.product_controller import ProductController

PRODUCT_ROUTER = Blueprint("product_router", __name__, url_prefix="/api/products")

@PRODUCT_ROUTER.route("", methods=["POST"])
async def create_product_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _Presenter: CreateProductPresenter = _ServiceProvider.get_service(CreateProductPresenter)
    _Presenter.get_route = get_products_async
    await _ProductController.create_product_async(CreateProductInputPort(**request.request_object), _Presenter)
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
