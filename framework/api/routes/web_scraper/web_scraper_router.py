from clapy import IServiceProvider
from flask import Blueprint, current_app, jsonify, request
from framework.api.infrastructure.request_object_decorator import request_object

from framework.api.routes.web_scraper.search_for_product_query import \
    SearchForProductQuery
from framework.api.view_models.product_view_model import get_product_view_model
from framework.api.view_models.scraped_product_offer_view_model import \
    get_scraped_product_offer_view_model
from framework.web_scraper.controller import WebScraper
from interface_adaptors.controllers.merchant_controller import \
    MerchantController
from interface_adaptors.controllers.product_controller import ProductController

WEB_SCRAPER_ROUTER = Blueprint("WEB_SCRAPER_ROUTER", __name__, url_prefix="/api/web-scraper")


# TODO: Possibly just belongs on the product router?? why make this distinction (feels bad tbh, shows implementation details)
# TODO Should use DI once web scraper is setup more clean, web scraper is a hosted service under the API
@WEB_SCRAPER_ROUTER.route("/search", methods=["POST"])
@request_object('search_for_product_async', SearchForProductQuery)
async def search_for_product_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _MerchantController: MerchantController = _ServiceProvider.get_service(MerchantController)
    _Query: SearchForProductQuery = request.request_object
    _Result = WebScraper(_MerchantController, _ProductController).search_for_product(_Query.search_term, _Query.start_page)
    return jsonify([get_scraped_product_offer_view_model(_Offer) for _Offer in _Result])

@WEB_SCRAPER_ROUTER.route("/offers", methods=["GET"])
async def get_product_offers_async():
    _ServiceProvider: IServiceProvider = current_app.service_provider
    _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    _MerchantController: MerchantController = _ServiceProvider.get_service(MerchantController)
    _Result = await WebScraper(_MerchantController, _ProductController).get_product_offers_async()
    return jsonify([get_product_view_model(_Product) for _Product in _Result])
