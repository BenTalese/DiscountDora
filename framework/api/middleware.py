from flask import Blueprint, jsonify, request
from varname import nameof

from framework.api.routes.products.create_product_command import \
    CreateProductCommand
from framework.api.routes.products.product_router import create_product_async
from framework.api.routes.web_scraper.search_for_product_query import \
    SearchForProductQuery
from framework.api.routes.web_scraper.web_scraper_router import \
    search_for_product_async

REQUEST_OBJECTS = {
    nameof(create_product_async): CreateProductCommand,
    nameof(search_for_product_async): SearchForProductQuery
}

middleware = Blueprint('middleware', __name__)

# TODO: ApiAuditing (make a metadata.db)

@middleware.before_app_request
async def handle_cors_preflight_request():
    if request.method.upper() == 'OPTIONS':
        return jsonify({
            'Access-Control-Allow-Origin': 'http://localhost:5174',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

# TODO: 400 bad request validation for required inputs

@middleware.before_app_request
async def deserialise_web_request():
    _RequestEndpoint = request.endpoint.split(".")[-1]
    if _RequestEndpoint in REQUEST_OBJECTS:
        deserialised_request = REQUEST_OBJECTS[_RequestEndpoint](**request.get_json())
        setattr(request, "request_object", deserialised_request)

# @middleware.after_app_request
# async def post_process(response: Response):
#     if "query" in request.view_args and (filter:= request.view_args["query"]):
#         x = 0

#     data = response.get_json()
#     response = response
