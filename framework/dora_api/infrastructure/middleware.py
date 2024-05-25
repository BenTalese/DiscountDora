import json
from base64 import b64decode
from http.client import BAD_REQUEST, NOT_FOUND
from typing import get_origin, get_type_hints

from clapy import AttributeChangeTracker
from flask import Blueprint, Response, jsonify, request

from application.infrastructure.utils import try_parse_uuid
from domain.entities.base_entity import EntityID
from framework.dora_api.infrastructure.base_presenter import ProblemDetails
from framework.dora_api.infrastructure.request_body_decorator import \
    REQUEST_BODYS_BY_ENDPOINT
from framework.dora_api.infrastructure.view_model_decorator import \
    VIEW_MODELS_BY_ENDPOINT

MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)

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

            if _AttributeTypeOrigin:= get_origin(_AttributeType):
                if _AttributeTypeOrigin is AttributeChangeTracker:
                    _DeserialisedRequestData[_AttributeName] = __get_deserialised_attribute_change_tracker(_AttributeName, _RequestData)

            elif _ParsedUUID := try_parse_uuid(_Data):
                _DeserialisedRequestData[_AttributeName] = EntityID(_ParsedUUID)

            elif _AttributeType is bytes and _Data:
                _DeserialisedRequestData[_AttributeName] = _AttributeType(b64decode(_Data))

            else:
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
        if _ParsedUUID := try_parse_uuid(request_data[attribute_name]):
            return AttributeChangeTracker(EntityID(_ParsedUUID), True)

        return AttributeChangeTracker(request_data[attribute_name])

#stock/id eq 1&other_property ne sometext
#GET /api/stock_items/filter=stock_item_id:eq:12345&sort=age_or_something:asc&page=1&limit=10
@MIDDLEWARE.after_app_request
async def apply_query_filter(response: Response):
    _Data: dict = response.get_json()

    if "query" in request.view_args and (_QueryString:= request.view_args["query"]):
        # TODO: Check property exists on request body, if not fail
        # TODO: Check if operator supported
        # TODO: Validate query string format is correct
        _QueryString: str
        _RequestEndpoint = request.endpoint.split(".")[-1]

        if _RequestEndpoint not in VIEW_MODELS_BY_ENDPOINT:
            x = 0 # TODO: DEV ERROR!

        _ViewModel = VIEW_MODELS_BY_ENDPOINT[_RequestEndpoint]

        _QueryOperations = _QueryString.split("&")

        _FilterOperations = [_Operation[7:] for _Operation in _QueryOperations if _Operation.startswith("filter=")]


        for _Filter in _FilterOperations:
            _Field, _Operator, _Value = _Filter.split(':')

            if _Operator == 'eq':
                _Data = [_Resource for _Resource in _Data if _Resource.get(_Field) == _Value]
            elif _Operator == 'lt':
                _Data = [_Resource for _Resource in _Data if _Resource.get(_Field) < _Value]
            elif _Operator == 'gt':
                _Data = [_Resource for _Resource in _Data if _Resource.get(_Field) > _Value]
            elif _Operator == 'le':
                _Data = [_Resource for _Resource in _Data if _Resource.get(_Field) <= _Value]
            elif _Operator == 'ge':
                _Data = [_Resource for _Resource in _Data if _Resource.get(_Field) >= _Value]
            elif _Operator == 'ne':
                _Data = [_Resource for _Resource in _Data if _Resource.get(_Field) != _Value]
            else:
                return jsonify(ProblemDetails(
                    detail = f"The filter operator {_Operator} is not supported. Supported operators"+\
                    " include 'eq', 'lt', 'gt', 'le', 'ge' and 'ne'.",
                    status = BAD_REQUEST,
                    errors = {},
                    title = "Filter operator not supported.",
                    type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1")), 400

        response.set_data(json.dumps(_Data))

    return response
