from typing import Any

from pydantic import BaseModel


RESPONSES_BY_ENDPOINT: dict[str, type[Any]] = {}


def has_response(response_class):
    """
    `has_response` is a decorator that registers an endpoint name against a response class,
    the purpose of which is to provide the response body to the query filtering middleware for
    validation.

    Using this decorator indicates this endpoint supports query filtering on the result set.
    """
    def decorator(func):
        RESPONSES_BY_ENDPOINT[func.__name__] = response_class
        return func
    return decorator


REQUEST_BODYS_BY_ENDPOINT: dict[str, type[BaseModel]] = {}


def has_request_body(request_body_class):
    """
    `has_request_body` is a decorator that registers an endpoint name against a request body class,
    the purpose of which is to provide the expected request body to the deserialisation middleware
    for incoming web requests.

    Using this decorator indicates this endpoint expects a request body.
    """
    def decorator(func):
        REQUEST_BODYS_BY_ENDPOINT[func.__name__] = request_body_class
        return func
    return decorator
