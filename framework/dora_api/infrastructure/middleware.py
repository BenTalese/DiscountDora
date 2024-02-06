from base64 import b64decode
from http.client import NOT_FOUND
from typing import get_origin, get_type_hints

from clapy import AttributeChangeTracker
from flask import Blueprint, jsonify, request

from framework.dora_api.infrastructure.base_presenter import ProblemDetails
from framework.dora_api.infrastructure.request_body_decorator import \
    REQUEST_BODYS_BY_ENDPOINT

MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)

# TODO: ApiAuditing (make a metadata.db)
# TODO: 400 bad request validation for required inputs

@MIDDLEWARE.before_app_request
async def handle_cors_preflight_request():
    if request.method.upper() == 'OPTIONS':
        return jsonify({
            'Access-Control-Allow-Origin': 'http://localhost:5174',
            'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

@MIDDLEWARE.before_app_request
async def verify_endpoint_exists():
    if not request.endpoint:
        return jsonify(ProblemDetails(
            detail = "Endpoint was not found.",
            status = NOT_FOUND,
            errors = {},
            title = "Endpoint was not found.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4")), 404

@MIDDLEWARE.before_app_request
async def deserialise_web_request():
    _RequestEndpoint = request.endpoint.split(".")[-1]
    if _RequestEndpoint in REQUEST_BODYS_BY_ENDPOINT:
        _RequestData: dict = request.get_json()
        _DeserialisedRequestData : dict = {}

        for _AttributeName, _AttributeType in get_type_hints(REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint]).items():
            _Data = _RequestData.get(_AttributeName)

            _AttributeTypeOrigin = get_origin(_AttributeType)
            if _AttributeTypeOrigin and _AttributeTypeOrigin is AttributeChangeTracker:
                _DeserialisedRequestData[_AttributeName] = __get_deserialised_attribute_change_tracker(_AttributeName, _RequestData)

            else:
                if _AttributeType is bytes:
                    _Data = b64decode(_Data)

                _DeserialisedRequestData[_AttributeName] = _AttributeType(_Data) if _Data else None

        _DeserialisedRequest = REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint](**_DeserialisedRequestData)
        setattr(request, "request_body", _DeserialisedRequest)

def __get_deserialised_attribute_change_tracker(attribute_name: str, request_data: dict) -> AttributeChangeTracker:
    '''
        Args:
            attribute_name (str): The name of the attribute which requires deserialisation.
            request_data (dict): The data which may contain the attribute_name as a key.

        Returns:
            AttributeChangeTracker: The deserialised value if attribute_name exists on request_data,
            otherwise the default AttributeChangeTracker.
    '''

    if attribute_name not in request_data.keys():
        return AttributeChangeTracker()

    elif request_data[attribute_name] is None:
        return AttributeChangeTracker(None, True)

    else:
        return AttributeChangeTracker(request_data[attribute_name])

# @middleware.after_app_request
# async def post_process(response: Response):
#     if "query" in request.view_args and (filter:= request.view_args["query"]):
#         x = 0

#     data = response.get_json()
#     response = response
