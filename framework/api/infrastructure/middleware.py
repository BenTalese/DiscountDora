from base64 import b64decode
from typing import get_origin, get_type_hints

from clapy import AttributeChangeTracker
from flask import Blueprint, jsonify, request

from framework.api.infrastructure.request_object_decorator import \
    REQUEST_OBJECTS_BY_ENDPOINT

MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)

# TODO: ApiAuditing (make a metadata.db)

@MIDDLEWARE.before_app_request
async def handle_cors_preflight_request():
    if request.method.upper() == 'OPTIONS':
        return jsonify({
            'Access-Control-Allow-Origin': 'http://localhost:5174',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

# TODO: 400 bad request validation for required inputs

@MIDDLEWARE.before_app_request
async def deserialise_web_request():
    _RequestEndpoint = request.endpoint.split(".")[-1]
    if _RequestEndpoint in REQUEST_OBJECTS_BY_ENDPOINT:
        _RequestData: dict = request.get_json()

        for _AttributeName, _AttributeType in get_type_hints(REQUEST_OBJECTS_BY_ENDPOINT[_RequestEndpoint]).items():

            _Data = _RequestData.get(_AttributeName)

            if issubclass(get_origin(_AttributeType), AttributeChangeTracker):
                __deserialise_attribute_change_tracker(_AttributeName, _RequestData)
                continue

            if _AttributeType is bytes:
                _Data = b64decode(_Data)

            _RequestData[_AttributeName] = _AttributeType(_Data) if _Data else None

        _DeserialisedRequest = REQUEST_OBJECTS_BY_ENDPOINT[_RequestEndpoint](**_RequestData)
        setattr(request, "request_object", _DeserialisedRequest)

def __deserialise_attribute_change_tracker(attribute_name: str, request_data: dict):
    '''
        Overrides, or sets the value of request_data[attribute_name] to the deserialised AttributeChangeTracker value.

        Args:
            attribute_name (str): The name of the attribute which requires deserialisation.
            request_data (dict): The data which may contain the attribute_name as a key.
    '''

    if attribute_name not in request_data.keys():
        request_data[attribute_name] = AttributeChangeTracker()

    elif request_data[attribute_name] is None:
        request_data[attribute_name] = AttributeChangeTracker(None, True)

    else:
        request_data[attribute_name] = AttributeChangeTracker(request_data[attribute_name])

# @middleware.after_app_request
# async def post_process(response: Response):
#     if "query" in request.view_args and (filter:= request.view_args["query"]):
#         x = 0

#     data = response.get_json()
#     response = response
