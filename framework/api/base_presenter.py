from abc import ABC
from dataclasses import dataclass
from http.client import BAD_REQUEST, CREATED, FORBIDDEN, INTERNAL_SERVER_ERROR, NO_CONTENT, NOT_FOUND, OK, UNAUTHORIZED, UNPROCESSABLE_ENTITY
from typing import Any, Callable, List, Tuple
import uuid

from flask import Response, jsonify, url_for
from clapy import (IAuthenticationOutputPort, IAuthorisationOutputPort,
                   IValidationOutputPort)
from clapy.outputs import AuthorisationResult, ValidationResult

from framework.api.view_models.created_view_model import CreatedViewModel

@dataclass
class ProblemDetails:
    detail: str = None
    errors: dict = {}
    status: int
    title: str = None
    type: str

class BasePresenter(
    IAuthenticationOutputPort,
    IAuthorisationOutputPort,
    IValidationOutputPort,
    ABC):
    result: Response
    _not_found_current_route_segment: int

    async def business_rule_violation_async(self, error_message: str) -> None:
        self.unprocessable_entity_async(ProblemDetails(
            detail = "See errors property for more details.",
            errors = { "": [error_message] },
            status = UNPROCESSABLE_ENTITY,
            title = "Business rule violation.",
            type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))

    async def bad_request_async(self, error_message: str):
        response = jsonify(ProblemDetails(
            detail = error_message,
            status = BAD_REQUEST,
            title = error_message,
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1"))
        response.content_type = 'application/problem+json'
        response.status_code = BAD_REQUEST
        self.result = response

    async def created_async(self, result: CreatedViewModel, get_route: Callable = None):
        response = jsonify(result)
        response.status_code = CREATED
        if get_route is not None:
            response.headers['Location'] = url_for(get_route.__name__, resource_id = result.id, _external=True)
        self.result = response

    async def entity_existence_failure_async(self, property_in_error: str, id: uuid.UUID):
        self.unprocessable_entity_async(ProblemDetails(
            detail = "See errors property for more details.",
            errors = { property_in_error: [f"A {property_in_error} with the ID '{id}' was not found."] },
            status = UNPROCESSABLE_ENTITY,
            title = "Entity was not found.",
            type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))

    async def entity_existence_failures_async(self, property_in_error: str, *ids: Tuple[uuid.UUID]):
        self.unprocessable_entity_async(ProblemDetails(
            detail = "See errors property for more details.",
            errors = { property_in_error: [f"{property_in_error}(s) with the ID(s) '{', '.join(*ids)}' were not found."] },
            status = UNPROCESSABLE_ENTITY,
            title = "Entity(s) were not found.",
            type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))

    async def internal_server_error_async(self, error_message: str):
        response = jsonify(ProblemDetails(
            detail = error_message,
            status = INTERNAL_SERVER_ERROR,
            title = "Internal server error.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.6.1"))
        response.content_type = 'application/problem+json'
        response.status_code = INTERNAL_SERVER_ERROR
        self.result = response

    async def no_content_async(self):
        response = Response(status = NO_CONTENT)
        response.status_code = NO_CONTENT
        self.result = response

    async def not_found_async(self, error_message: str, route_segment: int):
        if self._not_found_current_route_segment is None or route_segment < self._not_found_current_route_segment:
            self._not_found_current_route_segment = route_segment
            self.result = jsonify(ProblemDetails(
                detail = error_message,
                status = NOT_FOUND,
                title = "Entity was not found.",
                type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4"))

    async def ok_async(self, result: Any):
        response = jsonify(result)
        response.status_code = OK
        self.result = response

    async def present_unauthenticated_async(self):
        response = jsonify(ProblemDetails(
            detail = "Unauthenticated client.",
            status = UNAUTHORIZED,
            title = "Unauthenticated client.",
            type = "https://datatracker.ietf.org/doc/html/rfc7235#section-3.1"))
        response.content_type = 'application/problem+json'
        response.status_code = UNAUTHORIZED
        self.result = response

    async def present_unauthorised_async(self, authorisation_failure: AuthorisationResult):
        response = jsonify(ProblemDetails(
            detail = authorisation_failure.reason,
            status = FORBIDDEN,
            title = "Forbidden.",
            type = "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3"))
        response.content_type = 'application/problem+json'
        response.status_code = FORBIDDEN
        self.result = response

    async def present_validation_failure_async(self, validation_failure: ValidationResult):
        self.unprocessable_entity_async(ProblemDetails(
            detail = validation_failure.summary,
            status = UNPROCESSABLE_ENTITY,
            errors = validation_failure.errors,
            title = "Validation failure.",
            type = "https://datatracker.ietf.org/doc/html/rfc4918#section-11.2"))

    async def unprocessable_entity_async(self, problem_details: ProblemDetails): # TODO: THIS NEEDS TESTING, I DOUBT IT WORKS
        if self.result is None:
            response = jsonify(problem_details)
            response.content_type = 'application/problem+json'
            response.status_code = UNPROCESSABLE_ENTITY
            self.result = response
        elif self.result.data['status'] == UNPROCESSABLE_ENTITY:
            self.result.data['title'] = "Various errors."
            for property, error in problem_details.errors:
                if property in self.result.data['errors']:
                    self.result.data['errors'][property] = self.result.data['errors'][property] + error
                else:
                    self.result.data["errors"][property] = error
