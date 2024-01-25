REQUEST_OBJECTS_BY_ENDPOINT = {}

def request_object(endpoint_name, request_object_class):
    def decorator(func):
        REQUEST_OBJECTS_BY_ENDPOINT[endpoint_name] = request_object_class
        return func
    return decorator
