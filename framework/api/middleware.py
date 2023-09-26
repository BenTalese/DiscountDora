from flask import Blueprint, request
from varname import nameof

from framework.api.responses import bad_request
from framework.api.stock_items.request_objects import GetStockItemsQuery
from framework.api.stock_items.stock_items_controller import \
    get_stock_items_async

REQUEST_OBJECTS = {
    nameof(get_stock_items_async): GetStockItemsQuery
}

middleware = Blueprint('middleware', __name__)

# @middleware.before_app_request
# async def pre_process():
    # if request.endpoint not in REQUEST_OBJECTS:
    #     return bad_request() #TODO can't leave it as generic
    # data = {}
    # x = REQUEST_OBJECTS[request.endpoint](**data)
    # d = request.data
    # f = request.json
    # setattr(request, "request_object", REQUEST_OBJECTS[request.endpoint](**request.json))

@middleware.after_app_request
async def post_process(response):
    print(response)
