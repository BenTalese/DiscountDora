import json
import logging
from dataclasses import asdict
from http.client import BAD_REQUEST, NOT_FOUND
from typing import Any, get_type_hints

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from dora_api.infrastructure.api_response import (ProblemDetails, bad_request,
                                                  internal_server_error)
from dora_api.infrastructure.decorators import (REQUEST_BODYS_BY_ENDPOINT,
                                                RESPONSES_BY_ENDPOINT)


_Logger = logging.getLogger(__name__)
MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)


@MIDDLEWARE.before_app_request
def handle_incoming_request():
    if _Logger.isEnabledFor(logging.DEBUG):
        audit_incoming_request()

    if request.method.upper() == "OPTIONS":
        return handle_cors_preflight_request()

    if not request.endpoint:
        return jsonify(ProblemDetails(
            detail = "Endpoint was not found.",
            status = NOT_FOUND,
            errors = {},
            title = "Endpoint was not found.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4")), 404

    if request.method.upper() in ["POST", "PATCH", "PUT"]:
        return deserialise_web_request(request.endpoint.split(".")[-1])

    return


def audit_incoming_request():
    _Logger.debug(
        "Incoming request | method=%s path=%s endpoint=%s ip=%s",
        request.method,
        request.path,
        request.endpoint,
        request.remote_addr,
    )
    _Logger.debug(
        f"body: {request.get_json(silent=True)}" if request.is_json else ""
    )
    print(f"body: {request.get_json(silent=True)}" if request.is_json else "")


def handle_cors_preflight_request():
    return jsonify({
        'Access-Control-Allow-Origin': 'http://localhost:5174',
        'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    })


def deserialise_web_request(request_endpoint: str):
    if request_endpoint not in REQUEST_BODYS_BY_ENDPOINT:
        return internal_server_error("Endpoint not found in registry.")

    _RequestBodySchema = REQUEST_BODYS_BY_ENDPOINT[request_endpoint]
    try:
        _Parsed = _RequestBodySchema.model_validate(request.get_json())
    except ValidationError as e:
        _Errors = {
            ".".join(str(loc) for loc in err["loc"]): [err["msg"]]
            for err in e.errors()
        }
        return bad_request("Malformed request.", errors = _Errors)

    setattr(request, "request_body", _Parsed)


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
        return response

    if not (request.view_args and "query" in request.view_args and request.view_args["query"]):
        return response

    if response.status_code != 200:
        return response

    if not response.is_json:
        return response

    _ResponseData: list[dict[str, Any]] = response.get_json()

    if not isinstance(_ResponseData, list):
        return response

    _RequestEndpoint = request.endpoint.split(".")[-1]
    _QueryString: str = request.view_args["query"].lower()
    _QueryOperations: list[str] = _QueryString.split("&")

    if _RequestEndpoint not in RESPONSES_BY_ENDPOINT:
        set_bad_query_request_response(f'The endpoint "{_RequestEndpoint}" does not support filtering.')
        return response

    _ViewModel = RESPONSES_BY_ENDPOINT[_RequestEndpoint]
    _ViewModelFields = get_type_hints(_ViewModel)

    # ── FILTER OPERATION ──────────────────────────────────────────────────────

    _FilterOperations = [_Operation[7:] for _Operation in _QueryOperations if _Operation.startswith("filter=")]

    if _NonExistentFields := [
        _Operation.split(':')[0]
        for _Operation in _FilterOperations
        if _Operation.split(':')[0] not in _ViewModelFields
    ]:
        set_bad_query_request_response(f'Queried attribute(s) do not exist on response: {", ".join(_NonExistentFields)}.')
        return response

    for _Filter in _FilterOperations:
        _Parts = _Filter.split(':')
        if len(_Parts) != 3:
            set_bad_query_request_response(f"Malformed filter '{_Filter}'. Expected format: filter=field:operator:value.")
            return response

        _Field, _Operator, _Value = _Parts
        _Value = _Value.replace("_", " ").lower()

        def _get_field_value(resource: dict, field: str) -> str:
            _Val = resource.get(field)
            return "" if _Val is None else str(_Val).lower()

        match _Operator:
            case 'eq': _ResponseData = [r for r in _ResponseData if _get_field_value(r, _Field) == _Value]
            case 'ne': _ResponseData = [r for r in _ResponseData if _get_field_value(r, _Field) != _Value]
            case 'lt': _ResponseData = [r for r in _ResponseData if _get_field_value(r, _Field) < _Value]
            case 'gt': _ResponseData = [r for r in _ResponseData if _get_field_value(r, _Field) > _Value]
            case 'le': _ResponseData = [r for r in _ResponseData if _get_field_value(r, _Field) <= _Value]
            case 'ge': _ResponseData = [r for r in _ResponseData if _get_field_value(r, _Field) >= _Value]
            case 'ct': _ResponseData = [r for r in _ResponseData if _Value in _get_field_value(r, _Field)]
            case _:
                set_bad_query_request_response(
                    f"The filter operator '{_Operator}' is not supported. "
                    f"Supported operators: 'eq', 'ne', 'lt', 'gt', 'le', 'ge', 'ct'.")
                return response

    # ── SORT OPERATION ────────────────────────────────────────────────────────

    if _SortOperation := next((_Operation for _Operation in _QueryOperations if _Operation.startswith("sort=")), None):
        _SortParts = _SortOperation[5:].split(':')
        if len(_SortParts) != 2:
            set_bad_query_request_response(f"Malformed sort '{_SortOperation[5:]}'. Expected format: sort=field:asc|desc.")
            return response

        _SortField, _SortOrder = _SortParts

        if _SortField not in _ViewModelFields:
            set_bad_query_request_response(f"Sort field '{_SortField}' does not exist in the view model.")
            return response

        if _SortOrder not in ("asc", "desc"):
            set_bad_query_request_response(f"Sort order '{_SortOrder}' is not supported. Use 'asc' or 'desc'.")
            return response

        _ResponseData.sort(
            key=lambda resource: (resource.get(_SortField) is None, resource.get(_SortField, "")),
            reverse=_SortOrder == "desc"
        )

    # ── PAGINATION OPERATION ──────────────────────────────────────────────────

    _PageOperation = next((_Operation for _Operation in _QueryOperations if _Operation.startswith("page=")), None)
    _LimitOperation = next((_Operation for _Operation in _QueryOperations if _Operation.startswith("limit=")), None)

    if (_PageOperation is None) != (_LimitOperation is None):
        set_bad_query_request_response("You must use page and limit together.")
        return response

    if _PageOperation and _LimitOperation:
        try:
            _Page = int(_PageOperation[5:])
            _Limit = int(_LimitOperation[6:])
        except ValueError:
            set_bad_query_request_response("Page and limit must be integers.")
            return response

        if _Page < 1:
            set_bad_query_request_response("Page must be 1 or greater.")
            return response

        if _Limit < 1:
            set_bad_query_request_response("Limit must be 1 or greater.")
            return response

        _Start = (_Page - 1) * _Limit
        _End = _Start + _Limit
        _ResponseData = _ResponseData[_Start:_End]

    # ── SET RESPONSE ──────────────────────────────────────────────────────────

    response.set_data(json.dumps(_ResponseData))
    return response
