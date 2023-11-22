from flask import Blueprint, Response, jsonify, request
from varname import nameof

from framework.api.routes.products.create_product_command import \
    CreateProductCommand
from framework.api.routes.products.product_router import create_product_async
from framework.api.routes.web_scraper.search_for_product_query import SearchForProductCommand
from framework.api.routes.web_scraper.web_scraper_router import search_for_product_async

REQUEST_OBJECTS = {
    nameof(create_product_async): CreateProductCommand,
    nameof(search_for_product_async): SearchForProductCommand
}

middleware = Blueprint('middleware', __name__)

# TODO: ApiAuditing (make a metadata.db)

@middleware.before_app_request
async def add_cors_headers(response: Response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

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
