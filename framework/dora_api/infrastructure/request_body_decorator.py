REQUEST_BODYS_BY_ENDPOINT = {}

def has_request_body(endpoint_name, request_body_class):
    def decorator(func):
        REQUEST_BODYS_BY_ENDPOINT[endpoint_name] = request_body_class
        return func
    return decorator
