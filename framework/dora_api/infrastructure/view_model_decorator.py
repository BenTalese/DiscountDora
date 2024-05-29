VIEW_MODELS_BY_ENDPOINT = {}

def has_view_model(endpoint_name, view_model_class):
    """
    `has_view_model` is a decorator that registers an endpoint name against a view model class,
    the purpose of which is to provide the response body to the query filtering middleware for
    validation.

    Using this decorator indicates this endpoint supports query filtering.
    """
    def decorator(func):
        VIEW_MODELS_BY_ENDPOINT[endpoint_name] = view_model_class
        return func
    return decorator
