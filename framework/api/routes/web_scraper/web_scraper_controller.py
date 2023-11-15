from flask import Blueprint, current_app, jsonify, request

from framework.web_scraper.controller import search_for_product

web_scraper = Blueprint("web_scraper", __name__, url_prefix="/api/webScraper")

@web_scraper.route("/search", methods=["POST"])
async def search_for_product_async():
    x = search_for_product(request.get_json()['searchTerm'], request.get_json()['startPage'])
    for y in x:
        y.image = y.image.decode('utf-8') # TODO: do in view model mapping
    response = jsonify(x)
    return response
