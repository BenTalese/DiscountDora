from dataclasses import dataclass
from http.client import (BAD_REQUEST, CREATED, FORBIDDEN, INTERNAL_SERVER_ERROR,
                         NO_CONTENT, NOT_FOUND, OK, UNAUTHORIZED,
                         UNPROCESSABLE_ENTITY)
from typing import Any
from uuid import UUID

from flask import Response, jsonify, url_for


@dataclass
class ProblemDetails:
    detail: str
    status: int
    errors: dict
    title: str
    type: str


def business_rule_violation(error_message: str) -> Response:
    return unprocessable_entity(ProblemDetails(
        detail = "See errors property for more details.",
        status = UNPROCESSABLE_ENTITY,
        errors = {"": [error_message]},
        title = "Business rule violation.",
        type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))


def bad_request(title: str, detail: str | None = None, errors: dict[str, list[str]] = {}) -> Response:
    response = jsonify(ProblemDetails(
        detail = detail or "See errors property for more details.",
        errors = errors,
        status = BAD_REQUEST,
        title = title,
        type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"))
    response.content_type = 'application/problem+json'
    response.status_code = BAD_REQUEST
    return response


def created(
    resource_id: UUID,
    get_route: str,
    id_attribute_name: str,
    body: Any | None = None,
) -> Response:
    response = jsonify(body if body is not None else {'id': resource_id})
    response.status_code = CREATED
    response.headers['location'] = url_for(
        get_route,
        filter=f'{id_attribute_name}:eq:{resource_id}',
        _external=True,
    )
    return response


def entity_existence_failure(entity_name: str, property_in_error: str, id: UUID) -> Response:
    return unprocessable_entity(ProblemDetails(
        detail = "See errors property for more details.",
        errors = {property_in_error: [f"{entity_name} with the ID '{id}' was not found."]},
        status = UNPROCESSABLE_ENTITY,
        title = "Entity was not found.",
        type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))


def entity_existence_failures(entity_name: str, property_in_error: str, *ids: UUID) -> Response:
    return unprocessable_entity(ProblemDetails(
        detail = "See errors property for more details.",
        errors = {property_in_error: [f"{entity_name}(s) with the ID(s) '{', '.join(str(id) for id in ids)}' were not found."]},
        status = UNPROCESSABLE_ENTITY,
        title = "Entity(s) were not found.",
        type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))


def internal_server_error(error_message: str) -> Response:
    response = jsonify(ProblemDetails(
        detail = error_message,
        errors = {},
        status = INTERNAL_SERVER_ERROR,
        title = "Internal server error.",
        type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.6.1"))
    response.content_type = 'application/problem+json'
    response.status_code = INTERNAL_SERVER_ERROR
    return response


def no_content() -> Response:
    response = Response(status = NO_CONTENT)
    response.status_code = NO_CONTENT
    return response


def unauthorized(detail: str = "Authentication required.") -> Response:
    response = jsonify(ProblemDetails(
        detail = detail,
        errors = {},
        status = UNAUTHORIZED,
        title = "Unauthenticated.",
        type = "https://datatracker.ietf.org/doc/html/rfc7235#section-3.1"))
    response.content_type = 'application/problem+json'
    response.status_code = UNAUTHORIZED
    return response


def forbidden(detail: str = "You do not have permission to perform this action.") -> Response:
    response = jsonify(ProblemDetails(
        detail = detail,
        errors = {},
        status = FORBIDDEN,
        title = "Forbidden.",
        type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3"))
    response.content_type = 'application/problem+json'
    response.status_code = FORBIDDEN
    return response


def endpoint_not_found():
    """404 for an unknown/retired URL (no matching API endpoint). Plain
    `application/json` (not problem+json) to match what the request middleware
    already returns for no-route paths — shared so the SPA catch-all's
    `/api/...` branch produces the identical body for unmatched GETs (FU-167)
    instead of falling through to the default HTML 404."""
    return jsonify(ProblemDetails(
        detail = "Endpoint was not found.",
        status = NOT_FOUND,
        errors = {},
        title = "Endpoint was not found.",
        type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4")), NOT_FOUND


def not_found(entity_name: str, id: UUID) -> Response:
    response = jsonify(ProblemDetails(
        detail = f"{entity_name} with the ID '{id}' was not found.",
        errors = {},
        status = NOT_FOUND,
        title = "Entity was not found.",
        type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"))
    response.content_type = 'application/problem+json'
    response.status_code = NOT_FOUND
    return response


def ok(result: Any) -> Response:
    response = jsonify(result)
    response.status_code = OK
    return response


def paginated(items: list, total: int, page: int, limit: int) -> Response:
    response = jsonify({
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    })
    response.status_code = OK
    return response


def unprocessable_entity(problem_details: ProblemDetails) -> Response:
    response = jsonify(problem_details)
    response.content_type = 'application/problem+json'
    response.status_code = UNPROCESSABLE_ENTITY
    return response
    # TODO: Might want to reuse this (appending errors to same response)
    # elif self.result.json['status'] == UNPROCESSABLE_ENTITY:
    #     problem_details.title = "Various errors."

    #     _Errors = self.result.json['errors']

    #     for property, errors in _Errors.items():
    #         if property in problem_details.errors:
    #             for error in errors:
    #                 problem_details.errors[property].append(error)
    #         else:
    #             problem_details.errors[property] = errors

    #     response = jsonify(problem_details)
    #     response.content_type = 'application/problem+json'
    #     response.status_code = UNPROCESSABLE_ENTITY
    #     self.result = response


# TODO: Deal with these old responses

# def present_unauthenticated() -> Response:
#     response = jsonify(ProblemDetails(
#         detail = "Unauthenticated client.",
#         errors = {},
#         status = UNAUTHORIZED,
#         title = "Unauthenticated client.",
#         type = "https://datatracker.ietf.org/doc/html/rfc7235#section-3.1"))
#     response.content_type = 'application/problem+json'
#     response.status_code = UNAUTHORIZED
#     return response


# def present_unauthorised(authorisation_failure: AuthorisationResult) -> Response:
#     response = jsonify(ProblemDetails(
#         detail = authorisation_failure.reason,
#         errors = {},
#         status = FORBIDDEN,
#         title = "Forbidden.",
#         type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3"))
#     response.content_type = 'application/problem+json'
#     response.status_code = FORBIDDEN
#     return response


# def validation_failure(errors: dict[str, list[str]] = {}) -> Response:
#     return unprocessable_entity(ProblemDetails(
#         detail = "See errors property for more details.",
#         status = UNPROCESSABLE_ENTITY,
#         errors = errors,
#         title = "Validation failure.",
#         type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))
