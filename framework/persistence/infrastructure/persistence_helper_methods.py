import re
from typing import List, get_origin, get_type_hints

import sqlalchemy

from domain.entities.base_entity import EntityID


def is_entity(attribute_type):
    if get_origin(attribute_type) == list:
        attribute_type = attribute_type.__args__[0]
    return hasattr(attribute_type, "__module__") and "entities" in attribute_type.__module__ and attribute_type != EntityID

def is_list(attribute_type):
    return get_origin(attribute_type) == list

def is_model_attribute(model_type, attribute_name):
    return hasattr(getattr(getattr(model_type, attribute_name), "comparator"), "entity")

def is_model_list(value):
    return type(value) == sqlalchemy.orm.collections.InstrumentedList

def is_model(value):
    if is_model_list(value) and value:
        value = value[0]
    return hasattr(type(value), "__module__") and "models" in type(value).__module__

def get_model_type_from_attribute(model_type, attribute_name: str):
    if is_model_attribute(model_type, attribute_name):
        return getattr(model_type, attribute_name).comparator.entity.entity
    return None

# FIXME: This method works in a very strange way, needs refactoring
def translate_projection_source(projection_tree: dict, attributes: List[str], entity):
    def merge_nested_dicts(dict1: dict, dict2: dict):
        for key, value in dict2.items():
            if key not in dict1:
                dict1[key] = value
            else:
                merge_nested_dicts(dict1[key], value)

    if len(attributes) == 0:
        return {}

    attribute_name = attributes[0]
    attribute_type = get_type_hints(entity)[attribute_name]
    if len(attributes) == 1 and attribute_name in get_type_hints(entity).keys() and is_entity(attribute_type):
        entity_attributes = { attribute: {} for attribute in get_type_hints(attribute_type).keys() }
        if attribute_name not in projection_tree:
            projection_tree[attribute_name] = entity_attributes
        else:
            merge_nested_dicts(projection_tree[attribute_name], entity_attributes)

    elif attribute_name in projection_tree:
        source_to_merge = {}
        source_to_merge[attribute_name] = translate_projection_source({}, attributes[1:], attribute_type)
        merge_nested_dicts(projection_tree, source_to_merge)

    else:
        projection_tree[attribute_name] = translate_projection_source({}, attributes[1:], attribute_type)

    return projection_tree

def get_source_attribute_path(source_type, assignment_path_to_search: str):
    source_attributes = get_type_hints(source_type).items()
    for attribute_name, attribute_type in source_attributes:
        # If entity attribute in assignment, and no other attribute precedes this attribute (avoid 'other_entity.id' bug)
        pattern = r'(' + '|'.join(name for name, _ in source_attributes if name != attribute_name) + r')\.' + attribute_name
        potential_attributes = []
        for attribute in assignment_path_to_search.split("."): #TODO: There's gotta be regex for this...
            potential_attributes.extend(attribute.split())
        if attribute_name in potential_attributes and not re.search(pattern, assignment_path_to_search):
            if is_entity(attribute_type) and (child_attribute := get_source_attribute_path(attribute_type, assignment_path_to_search)):
                return attribute_name + "." + child_attribute
            return attribute_name
    return ""

def cast_to_new_model(model_from_row_result, projection_structure: dict, cast_destination_model):
    for attribute_name, child_attributes in projection_structure.items():
        if not child_attributes:
            setattr(cast_destination_model, attribute_name, getattr(model_from_row_result, attribute_name))
        else:
            linked_model_from_row_result = getattr(model_from_row_result, attribute_name)
            if not linked_model_from_row_result:
                continue
            if type(linked_model_from_row_result) == sqlalchemy.orm.collections.InstrumentedList:
                child_models = []
                for linked_model_from_list_result in linked_model_from_row_result:
                    linked_model = get_model_type_from_attribute(type(cast_destination_model), attribute_name)()
                    cast_to_new_model(linked_model_from_list_result, child_attributes, linked_model)
                    child_models.append(linked_model)
                setattr(cast_destination_model, attribute_name, child_models)
            else:
                linked_model = get_model_type_from_attribute(type(cast_destination_model), attribute_name)()
                cast_to_new_model(linked_model_from_row_result, child_attributes, linked_model)
                setattr(cast_destination_model, attribute_name, linked_model)
