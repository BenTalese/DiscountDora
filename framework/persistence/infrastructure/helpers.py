from typing import get_origin

from domain.entities.base_entity import EntityID


def is_entity(attribute_type):
    if get_origin(attribute_type) == list:
        attribute_type = attribute_type.__args__[0]
    return hasattr(attribute_type, "__module__") and "entities" in attribute_type.__module__ and attribute_type != EntityID

def is_list(attribute_type):
    return get_origin(attribute_type) == list

def is_model(model_type, attribute_name):
    return hasattr(getattr(getattr(model_type, attribute_name), "comparator"), "entity")
