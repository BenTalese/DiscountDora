import json
from base64 import b64decode
from dataclasses import asdict
from http.client import BAD_REQUEST, NOT_FOUND
import logging
from typing import Any, Dict, List, get_origin, get_type_hints

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
# TODO: data = request.form.to_dict() (DESERIALISE FORM DATA, maybe not needed)


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
    def malformed_request(errors: Dict[str, str]):
        _ProblemDetails = ProblemDetails(
            detail = "See errors property for more details.",
            status = BAD_REQUEST,
            errors = errors,
            title = "Malformed request. One or more request properties could not be deserialised.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1")

        return _ProblemDetails

    _RequestEndpoint = request.endpoint.split(".")[-1]
    if _RequestEndpoint in REQUEST_BODYS_BY_ENDPOINT:
        _RequestData: dict = request.get_json()
        _DeserialisedRequestData: dict = {}
        _RequestBodySchema = get_type_hints(REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint]).items()
        _Errors: Dict[str, str] = {}

        for _AttributeName, _AttributeType in _RequestBodySchema:
            try:
                _Data = _RequestData.get(_AttributeName)

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
                _Errors[_AttributeName] = f"Expected type '{_AttributeType}'. " + str(e)
                logging.getLogger(__name__).exception(e)

        if _Errors:
            return jsonify(malformed_request(_Errors)), 400

        _DeserialisedRequest = REQUEST_BODYS_BY_ENDPOINT[_RequestEndpoint](**_DeserialisedRequestData)

        '''Remove attributes not present in request data to allow RequiredInputValidator pipe to work.
            Will leave AttributeChangeTrackers, unintentionally avoiding null exceptions, e.g. "price.has_been_set".
            This may cause several bugs in the future if 'delattr' changes its behaviour.'''
        for _AttributeName, _ in _RequestBodySchema:
            if _AttributeName not in _RequestData:
                delattr(_DeserialisedRequest, _AttributeName)

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
async def apply_query_operations(response: Response):
    def bad_query_request(message: str):
        _ProblemDetails = ProblemDetails(
            detail = message,
            status = BAD_REQUEST,
            errors = {},
            title = "Unsupported query operation.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1")

        response.set_data(json.dumps(asdict(_ProblemDetails)))
        response.status_code = 400
        response.headers["Content-Type"] = "application/problem+json"

    if request.view_args and "query" in request.view_args.keys() and (_QueryString := request.view_args["query"]):
        _ResponseData: List[Dict[str, Any]] = response.get_json()
        _RequestEndpoint = request.endpoint.split(".")[-1]
        _QueryString: str = _QueryString.lower()
        _QueryOperations: List[str] = _QueryString.split("&")

        if _RequestEndpoint not in VIEW_MODELS_BY_ENDPOINT:
            bad_query_request(f'The endpoint "{_RequestEndpoint}" does not support filtering.')
            return response

        _ViewModel = VIEW_MODELS_BY_ENDPOINT[_RequestEndpoint]

        # FILTER OPERATION
        _FilterOperations = [_Operation[7:] for _Operation in _QueryOperations if _Operation.startswith("filter=")]
        if _NonExistentFields := [
            _Operation.split(':')[0]
            for _Operation
            in _FilterOperations
            if _Operation.split(':')[0] not in get_type_hints(_ViewModel)
        ]:
            bad_query_request(f'Queried attribute(s) do not exist on response: {", ".join(_NonExistentFields)}.')
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
                    bad_query_request(f"The filter operator {_Operator} is not supported. Supported operators"
                                      + " include 'eq', 'lt', 'gt', 'le', 'ge', 'ne' and 'ct'.")
                    return response

        # SORT OPERATION
        if _SortOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("sort=")), None):
            _SortField, _SortOrder = _SortOperation[5:].split(':')

            if _SortField not in get_type_hints(_ViewModel):
                bad_query_request(f"Sort field '{_SortField}' does not exist in the view model.")
                return response

            _ResponseData.sort(key = lambda resource: resource.get(_SortField), reverse = _SortOrder == 'desc')

        # PAGINATION OPERATION
        _Page: int = None
        _Limit: int = None

        if _PageOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("page=")), None):
            try:
                _Page = int(_PageOperation[5:])
            except ValueError:
                bad_query_request("The page parameter must be an integer.")
                return response

        if _LimitOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("limit=")), None):
            try:
                _Limit = int(_LimitOperation[6:])
            except ValueError:
                bad_query_request("The limit parameter must be an integer.")
                return response

        if (_PageOperation is None) != (_LimitOperation is None):
            bad_query_request("You must use page and limit operations together.")
            return response

        if _PageOperation and _LimitOperation:
            _Start = (_Page - 1) * _Limit
            _End = _Start + _Limit
            _ResponseData = _ResponseData[_Start:_End]

        # SET RESPONSE
        response.set_data(json.dumps(_ResponseData))

    return response
