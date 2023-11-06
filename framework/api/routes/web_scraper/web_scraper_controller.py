from flask import Blueprint, current_app, jsonify, request

from framework.web_scraper.controller import Controller

web_scraper = Blueprint("web_scraper", __name__, url_prefix="/api/webScraper")

@web_scraper.route("/doTheThing", methods=["POST"])
async def do_the_thing():
    x = Controller.search_for_product(request.get_json()['searchTerm'], request.get_json()['startPage'])
    response = jsonify({"data": "Your data here"})
    return response
