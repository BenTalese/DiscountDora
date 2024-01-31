from base64 import b64decode
from typing import get_type_hints

from flask import Blueprint, jsonify, request

from framework.dora_api.infrastructure.request_body_decorator import \
    REQUEST_BODYS_BY_ENDPOINT

MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)

# TODO: ApiAuditing (make a metadata.db)

@MIDDLEWARE.before_app_request
async def handle_cors_preflight_request():
    if request.method.upper() == 'OPTIONS':
        return jsonify({
            'Access-Control-Allow-Origin': 'http://localhost:5174',
            'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

# TODO: 400 bad request validation for required inputs

@MIDDLEWARE.before_app_request
async def deserialise_web_request():
    _RequestEndpoint = request.endpoint.split(".")[-1]
    if _RequestEndpoint in REQUEST_BODYS_BY_ENDPOINT:
        _RequestData: dict = request.get_json()

        for _AttributeName, _AttributeType in get_type_hints(REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint]).items():
            _Data = _RequestData[_AttributeName]

            if _AttributeType is bytes:
                _Data = b64decode(_Data)

            _RequestData[_AttributeName] = _AttributeType(_Data) if _Data else None

        _DeserialisedRequest = REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint](**_RequestData)
        setattr(request, "request_body", _DeserialisedRequest)

# @middleware.after_app_request
# async def post_process(response: Response):
#     if "query" in request.view_args and (filter:= request.view_args["query"]):
#         x = 0

#     data = response.get_json()
#     response = response
