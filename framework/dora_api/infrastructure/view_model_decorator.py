VIEW_MODELS_BY_ENDPOINT = {}

def has_view_model(endpoint_name, view_model_class):
    def decorator(func):
        VIEW_MODELS_BY_ENDPOINT[endpoint_name] = view_model_class
        return func
    return decorator
