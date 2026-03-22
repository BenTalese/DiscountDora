import importlib
import inspect
import os
import re
from pathlib import Path
from typing import Any, List, TypeGuard

from pydantic import BaseModel

from dora_api.domain.generics import TValue
from dora_api.domain.types import Unset
from dora_api.infrastructure.dependency_container import DependencyContainer


def apply_exclusion_filter(collection: List[str], exclusion_patterns: List[str]) -> None:
    '''
    Summary
    -------
    Applies RegEx exclusion patterns to a collection of strings and removes any
    items that match those patterns.

    Parameters
    ----------
    `collection` A list of strings that represents the collection of items that need
    to be filtered.\n
    `exclusion_patterns` A list of regular expression patterns that should be used to exclude
    certain items from the collection.

    Example
    -------
    my_collection = ["a", "b", "c", "d"]\n
    exclusion_patterns = ["b", "d"]\n
    MyClass.apply_exclusion_filter(my_collection, exclusion_patterns)\n
    print(my_collection)  # Output: ["a", "c"]

    '''
    for _ExclusionPattern in exclusion_patterns:
        collection[:] = [_Item for _Item in collection if not re.match(_ExclusionPattern, _Item)]


def get_classes_ending_with(term: str, path_to_search: Path | str):
    _Classes = []

    for _Root, _Directories, _Files in os.walk(path_to_search):

        DIR_EXCLUSIONS = [r"__pycache__"]
        FILE_EXCLUSIONS = [r".*__init__\.py", r"^.*(?<!\.py)$"]
        apply_exclusion_filter(_Directories, DIR_EXCLUSIONS)
        apply_exclusion_filter(_Files, FILE_EXCLUSIONS)

        _Namespace = _Root.replace('/', '.').replace('\\', '.').lstrip(".")
        for _File in _Files:
            _Module = importlib.import_module(f"{_Namespace}.{_File[:-3]}", package=None)
            [_Classes.append((_Class))
                for _, _Class
                in inspect.getmembers(_Module, inspect.isclass)
                if _Class.__name__.lower().endswith(term.lower())]

    return _Classes


def get_attributes_ending_with(term: str, path_to_search: Path | str):
    _Attributes = []

    for _Root, _Directories, _Files in os.walk(path_to_search):

        DIR_EXCLUSIONS = [r"__pycache__"]
        FILE_EXCLUSIONS = [r".*__init__\.py", r"^.*(?<!\.py)$"]
        apply_exclusion_filter(_Directories, DIR_EXCLUSIONS)
        apply_exclusion_filter(_Files, FILE_EXCLUSIONS)

        _Namespace = _Root.replace('/', '.').replace('\\', '.').lstrip(".")
        for _File in _Files:
            _Module = importlib.import_module(f"{_Namespace}.{_File[:-3]}", package=None)
            for _AttributeName, _AttributeValue in inspect.getmembers(_Module):
                if _AttributeName.lower().endswith(term.lower()) and _AttributeValue not in _Attributes:
                    _Attributes.append((_AttributeValue))

    return _Attributes


def field_of(model: type[BaseModel], field: str) -> str:
    if field not in model.model_fields:
        raise ValueError(f"'{field}' is not a field on '{model.__name__}'")
    return field


def is_set(value: TValue | Unset) -> TypeGuard[TValue]:
    return not isinstance(value, Unset)


def get_request_body() -> Any:
    '''
    Retrieves the request body from the current Flask request context.

    Returns:
        The deserialized request body, or None if no request body is present.
    '''
    from flask import request
    return getattr(request, 'request_body', None)


def get_container() -> DependencyContainer:
    '''
    Retrieves the dependency container from the current Flask application context.

    Returns:
        The dependency container instance, or None if not found.
    '''
    from flask import current_app
    return getattr(current_app, 'container')
