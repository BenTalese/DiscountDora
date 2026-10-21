from pydantic import BaseModel


REQUEST_BODYS_BY_ENDPOINT: dict[str, type[BaseModel]] = {}


def has_request_body(request_body_class: type[BaseModel]):
    """Registers an endpoint's expected request body schema with the
    deserialisation middleware. Endpoints without this decorator are treated
    as accepting no body.
    """
    def decorator(func):
        REQUEST_BODYS_BY_ENDPOINT[func.__name__] = request_body_class
        return func
    return decorator
