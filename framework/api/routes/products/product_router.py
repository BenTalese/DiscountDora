from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify, request
from varname import nameof

from application.use_cases.products.create_product.create_product_input_port import \
    CreateProductInputPort
from domain.entities.base_entity import EntityID
from framework.api.infrastructure.request_object_decorator import \
    request_object
from framework.api.routes.products.create_product_command import \
    CreateProductCommand
from framework.api.routes.products.create_product_presenter import \
    CreateProductPresenter
from framework.api.routes.products.get_products_presenter import \
    GetProductsPresenter
from framework.api.routes.products.search_for_product_query import \
    SearchForProductQuery
from framework.api.view_models.product_view_model import get_product_view_model
from framework.api.view_models.scraped_product_offer_view_model import \
    get_scraped_product_offer_view_model
from framework.web_scraper.controller import WebScraper
from interface_adaptors.controllers.merchant_controller import \
    MerchantController
from interface_adaptors.controllers.product_controller import ProductController

PRODUCT_ROUTER = Blueprint("PRODUCT_ROUTER", __name__, url_prefix="/api/products")


#TODO: probably want to have map methods (e.g. get_create_product_input_port()) instead of doing mapping directly in route method
@PRODUCT_ROUTER.route("")
@PRODUCT_ROUTER.route("<query>")
async def get_products_async(query = None):
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _Presenter: GetProductsPresenter = _ServiceProvider.get_service(GetProductsPresenter)

    await _ProductController.get_products_async(_Presenter)
    return _Presenter.result


@PRODUCT_ROUTER.route("", methods=["POST"])
@request_object('create_product_async', CreateProductCommand)
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


@PRODUCT_ROUTER.route("/offers", methods=["GET"])
async def get_product_offers_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _MerchantController: MerchantController = _ServiceProvider.get_service(MerchantController)
    _Result = await WebScraper(_MerchantController, _ProductController).get_product_offers_async()
    return jsonify([get_product_view_model(_Product) for _Product in _Result])


# TODO Should use DI once web scraper is setup more clean, web scraper is a hosted service under the API
@PRODUCT_ROUTER.route("/search", methods=["POST"])
@request_object('search_for_product_async', SearchForProductQuery)
async def search_for_product_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _MerchantController: MerchantController = _ServiceProvider.get_service(MerchantController)
    _Query: SearchForProductQuery = request.request_object
    _Result = WebScraper(_MerchantController, _ProductController).search_for_product(_Query.search_term, _Query.start_page)
    return jsonify([get_scraped_product_offer_view_model(_Offer) for _Offer in _Result])


