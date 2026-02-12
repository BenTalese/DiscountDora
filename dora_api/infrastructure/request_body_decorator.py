REQUEST_BODYS_BY_ENDPOINT = {}


def has_request_body(endpoint_name, request_body_class):
    """
    `has_request_body` is a decorator that registers an endpoint name against a request body class,
    the purpose of which is to provide the expected request body to the deserialisation middleware
    for incoming web requests.

    Using this decorator indicates this endpoint expects a request body.
    """
    def decorator(func):
        REQUEST_BODYS_BY_ENDPOINT[endpoint_name] = request_body_class
        return func
    return decorator
