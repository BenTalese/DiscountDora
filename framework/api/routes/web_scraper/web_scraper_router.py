from flask import Blueprint, jsonify, request

from framework.api.routes.web_scraper.search_for_product_query import \
    SearchForProductQuery
from framework.api.view_models.scraped_product_offer_view_model import \
    get_scraped_product_offer_view_model
from framework.web_scraper.controller import search_for_product

web_scraper_router = Blueprint("web_scraper_router", __name__, url_prefix="/api/webScraper")

@web_scraper_router.route("/search", methods=["POST"])
async def search_for_product_async():
    # _ServiceProvider: IServiceProvider = current_app.service_provider
    # _ProductController: ProductController = _ServiceProvider.get_service(ProductController)
    # _Presenter: CreateProductPresenter = _ServiceProvider.get_service(CreateProductPresenter)
    # await _ProductController.create_product_async(CreateProductInputPort(**request.request_object), _Presenter)
    # return _Presenter.result
    query: SearchForProductQuery = request.request_object
    result = search_for_product(query.search_term, query.start_page)
    return jsonify([get_scraped_product_offer_view_model(offer) for offer in result])
