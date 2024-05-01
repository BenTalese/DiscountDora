VIEW_MODELS_BY_ENDPOINT = {}

# TODO: Document what this is and why use it/what it affects
def has_view_model(endpoint_name, view_model_class):
    def decorator(func):
        VIEW_MODELS_BY_ENDPOINT[endpoint_name] = view_model_class
        return func
    return decorator
