from clapy import IServiceProvider
from flask import Blueprint, current_app, request
from varname import nameof

from application.use_cases.products.create_product.create_product_input_port import \
    CreateProductInputPort
from application.use_cases.products.update_product.update_product_input_port import \
    UpdateProductInputPort
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.command_mapper import \
    get_input_port_from_command
from framework.dora_api.infrastructure.request_body_decorator import \
    has_request_body
from framework.dora_api.infrastructure.view_model_decorator import has_view_model
from framework.dora_api.routes.products.create_product_command import \
    CreateProductCommand
from framework.dora_api.routes.products.create_product_presenter import \
    CreateProductPresenter
from framework.dora_api.routes.products.get_products_presenter import \
    GetProductsPresenter
from framework.dora_api.routes.products.update_product_command import \
    UpdateProductCommand
from framework.dora_api.routes.products.update_product_presenter import \
    UpdateProductPresenter
from framework.dora_api.view_models.product_view_model import ProductViewModel
from interface_adaptors.controllers.product_controller import ProductController

PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")



@PRODUCT_ROUTER.route("", methods=["POST"])
@has_request_body('create_product_async', CreateProductCommand)
async def create_product_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _Presenter: CreateProductPresenter = _ServiceProvider.get_service(CreateProductPresenter)

    _Command: CreateProductCommand = request.request_body
    _Presenter.request_body: CreateProductCommand = _Command
    _Presenter.get_route = f"{nameof(PRODUCT_ROUTER)}.{nameof(get_products_async)}"
    _InputPort = CreateProductInputPort(
        brand = _Command.brand,
        image = _Command.image,
        is_active = _Command.is_active,
        is_available = _Command.is_available,
        merchant_name = _Command.merchant_name,
        merchant_stockcode = _Command.merchant_stockcode,
        name = _Command.name,
        price_now = _Command.price_now,
        price_was = _Command.price_was,
        size = _Command.size,
        size_unit = _Command.size_unit,
        size_value = _Command.size_value,
        web_url = _Command.web_url)

    await _ProductController.create_product_async(_InputPort, _Presenter)
    return _Presenter.result


@PRODUCT_ROUTER.route("")
@PRODUCT_ROUTER.route("<query>")
@has_view_model('get_products_async', ProductViewModel)
async def get_products_async(query = None):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _Presenter: GetProductsPresenter = _ServiceProvider.get_service(GetProductsPresenter)

    await _ProductController.get_products_async(_Presenter)
    return _Presenter.result


@PRODUCT_ROUTER.route("/<product_id>", methods=["PATCH"])
@has_request_body("update_product_async", UpdateProductCommand)
async def update_product_async(product_id):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _Presenter: UpdateProductPresenter = _ServiceProvider.get_service(UpdateProductPresenter)

    _Command: UpdateProductCommand = request.request_body
    _InputPort: UpdateProductInputPort = UpdateProductInputPort(
        is_active = _Command.is_active,
        is_available = _Command.is_available,
        price_now = _Command.price_now,
        price_was = _Command.price_was,
        product_id = EntityID(product_id))

    await _ProductController.update_product_async(_InputPort, _Presenter)
    return _Presenter.result
