from abc import ABC
from http.client import OK
from typing import Any

from flask import Response, jsonify
from clapy import (IAuthenticationOutputPort, IAuthorisationOutputPort,
                   IValidationOutputPort)
from clapy.outputs import AuthorisationResult, ValidationResult


class BasePresenter(
    IAuthenticationOutputPort,
    IAuthorisationOutputPort,
    IValidationOutputPort,
    ABC):
    result: Response

    async def bad_request_async(self):
        raise NotImplementedError()

    async def created_async(self):
        raise NotImplementedError()

    async def entity_existence_failure_async(self):
        raise NotImplementedError()

    async def file_async(self):
        raise NotImplementedError()

    async def forbidden_async(self):
        raise NotImplementedError()

    async def internal_server_error_async(self):
        raise NotImplementedError()

    async def no_content_async(self):
        raise NotImplementedError()

    async def not_found_async(self):
        raise NotImplementedError()

    async def ok_async(self, result: Any):
        response = jsonify(result)
        response.status_code = OK
        self.result = response

    async def present_unauthenticated_async(self):
        raise NotImplementedError()

    async def present_unauthorised_async(self, authorisation_failure: AuthorisationResult):
        raise NotImplementedError()

    async def present_validation_failure_async(self, validation_failure: ValidationResult):
        raise NotImplementedError()

    async def unauthorised_async(self):
        raise NotImplementedError()

    async def unprocessable_entity_async(self):
        raise NotImplementedError()
