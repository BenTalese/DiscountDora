import json
import logging
from base64 import b64decode
from dataclasses import asdict
from http.client import BAD_REQUEST, NOT_FOUND
from typing import Any, Dict, List, get_origin, get_type_hints

from flask import Blueprint, Response, jsonify, request

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.types import AttributeChangeTracker
from dora_api.infrastructure.api_response import ProblemDetails, bad_request
from dora_api.infrastructure.decorators import (REQUEST_BODYS_BY_ENDPOINT,
                                                RESPONSES_BY_ENDPOINT)
from dora_api.infrastructure.utils import try_parse_uuid, unwrap_optional
from dora_api.infrastructure.validators import validate_inputs

MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)


@MIDDLEWARE.before_app_request
def handle_cors_preflight_request():
    if request.method.upper() == 'OPTIONS':
        return jsonify({
            'Access-Control-Allow-Origin': 'http://localhost:5174',
            'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })


@MIDDLEWARE.before_app_request
def verify_endpoint_exists():
    if not request.endpoint:
        return jsonify(ProblemDetails(
            detail = "Endpoint was not found.",
            status = NOT_FOUND,
            errors = {},
            title = "Endpoint was not found.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4")), 404


@MIDDLEWARE.before_app_request
def deserialise_web_request():
    if request.endpoint is None:
        return

    _RequestEndpoint = request.endpoint.split(".")[-1]
    if _RequestEndpoint in REQUEST_BODYS_BY_ENDPOINT:
        _RequestData: dict = request.get_json()
        _DeserialisedRequestData: dict = {}
        _RequestBodySchema = get_type_hints(REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint]).items()
        _Errors: dict[str, list[str]] = {}

        _SchemaKeys = {key for key, _ in _RequestBodySchema}
        for _Key in _RequestData.keys():
            if _Key not in _SchemaKeys:
                _Errors[_Key] = [f"Unexpected value '{_Key}' not found in schema '{REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint]}'."]

        for _AttributeName, _AttributeType in _RequestBodySchema:
            try:
                _Data = _RequestData.get(_AttributeName)
                _AttributeType = unwrap_optional(_AttributeType)

                if _AttributeTypeOrigin := get_origin(_AttributeType):
                    if _AttributeTypeOrigin is AttributeChangeTracker:
                        _DeserialisedRequestData[_AttributeName] = __get_deserialised_attribute_change_tracker(_AttributeName, _RequestData)

                elif _ParsedUUID := try_parse_uuid(_Data):
                    _DeserialisedRequestData[_AttributeName] = EntityID(_ParsedUUID)

                elif _AttributeType is bytes and _Data:
                    _DeserialisedRequestData[_AttributeName] = _AttributeType(b64decode(_Data))

                else:
                    _DeserialisedRequestData[_AttributeName] = _AttributeType(_Data) if _Data else None

            except (ValueError, TypeError, AttributeError) as e:
                _Errors[_AttributeName] = [f"Expected type '{_AttributeType}'. " + str(e)]
                logging.getLogger(__name__).exception(e)

        if _Errors:
            return bad_request("Malformed request. One or more request properties could not be deserialised.", errors = _Errors)

        _DeserialisedRequest = REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint](**_DeserialisedRequestData)

        '''Remove attributes not present in request data to allow validate_inputs to work.
            Will leave AttributeChangeTrackers, unintentionally avoiding null exceptions, e.g. "price.has_been_set".
            This may cause several bugs in the future if 'delattr' changes its behaviour.'''
        for _AttributeName, _ in _RequestBodySchema:
            if _AttributeName not in _RequestData:
                delattr(_DeserialisedRequest, _AttributeName)

        _ValidationResult = validate_inputs(_DeserialisedRequest)

        if _ValidationResult is not None:
            return bad_request(_ValidationResult.summary, errors = _ValidationResult.errors)

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


@MIDDLEWARE.after_app_request
def apply_query_operations(response: Response):
    def set_bad_query_request_response(message: str):
        _ProblemDetails = ProblemDetails(
            detail = message,
            status = BAD_REQUEST,
            errors = {},
            title = "Unsupported query operation.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1")

        response.set_data(json.dumps(asdict(_ProblemDetails)))
        response.status_code = 400
        response.headers["Content-Type"] = "application/problem+json"

    if request.endpoint is None:
        return

    if request.view_args and "query" in request.view_args.keys() and (_QueryString := request.view_args["query"]):
        _ResponseData: List[Dict[str, Any]] = response.get_json()
        _RequestEndpoint = request.endpoint.split(".")[-1]
        _QueryString: str = _QueryString.lower()
        _QueryOperations: List[str] = _QueryString.split("&")

        if _RequestEndpoint not in RESPONSES_BY_ENDPOINT:
            set_bad_query_request_response(f'The endpoint "{_RequestEndpoint}" does not support filtering.')
            return response

        _ViewModel = RESPONSES_BY_ENDPOINT[_RequestEndpoint]

        # FILTER OPERATION
        _FilterOperations = [_Operation[7:] for _Operation in _QueryOperations if _Operation.startswith("filter=")]
        if _NonExistentFields := [
            _Operation.split(':')[0]
            for _Operation
            in _FilterOperations
            if _Operation.split(':')[0] not in get_type_hints(_ViewModel)
        ]:
            set_bad_query_request_response(f'Queried attribute(s) do not exist on response: {", ".join(_NonExistentFields)}.')
            return response

        for _Filter in _FilterOperations:
            _Field, _Operator, _Value = _Filter.split(':')
            _Value = _Value.replace("_", " ").lower()

            match _Operator:
                case 'eq':
                    _ResponseData = [_Resource for _Resource in _ResponseData if str(_Resource.get(_Field)).lower() == _Value]
                case 'lt':
                    _ResponseData = [_Resource for _Resource in _ResponseData if str(_Resource.get(_Field)).lower() < _Value]
                case 'gt':
                    _ResponseData = [_Resource for _Resource in _ResponseData if str(_Resource.get(_Field)).lower() > _Value]
                case 'le':
                    _ResponseData = [_Resource for _Resource in _ResponseData if str(_Resource.get(_Field)).lower() <= _Value]
                case 'ge':
                    _ResponseData = [_Resource for _Resource in _ResponseData if str(_Resource.get(_Field)).lower() >= _Value]
                case 'ne':
                    _ResponseData = [_Resource for _Resource in _ResponseData if str(_Resource.get(_Field)).lower() != _Value]
                case 'ct':
                    _ResponseData = [_Resource for _Resource in _ResponseData if _Value in str(_Resource.get(_Field)).lower()]

                case _:
                    set_bad_query_request_response(f"The filter operator {_Operator} is not supported. Supported operators"
                                                   + " include 'eq', 'lt', 'gt', 'le', 'ge', 'ne' and 'ct'.")
                    return response

        # SORT OPERATION
        if _SortOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("sort=")), None):
            _SortField, _SortOrder = _SortOperation[5:].split(':')

            if _SortField not in get_type_hints(_ViewModel):
                set_bad_query_request_response(f"Sort field '{_SortField}' does not exist in the view model.")
                return response

            _ResponseData.sort(
                key=lambda resource: resource.get(_SortField, ""),
                reverse=_SortOrder == "desc"
            )

        # PAGINATION OPERATION
        _Page: int = 0
        _Limit: int = 0

        if _PageOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("page=")), None):
            try:
                _Page = int(_PageOperation[5:])
            except ValueError:
                set_bad_query_request_response("The page parameter must be an integer.")
                return response

        if _LimitOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("limit=")), None):
            try:
                _Limit = int(_LimitOperation[6:])
            except ValueError:
                set_bad_query_request_response("The limit parameter must be an integer.")
                return response

        if (_PageOperation is None) != (_LimitOperation is None):
            set_bad_query_request_response("You must use page and limit operations together.")
            return response

        if _PageOperation and _LimitOperation:
            _Start = (_Page - 1) * _Limit
            _End = _Start + _Limit
            _ResponseData = _ResponseData[_Start:_End]

        # SET RESPONSE
        response.set_data(json.dumps(_ResponseData))

    return response
