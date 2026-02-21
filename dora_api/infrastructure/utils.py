import importlib
import inspect
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from clapy import Common

from dora_api.infrastructure.dependency_container import DependencyContainer


def get_classes_ending_with(term: str, path_to_search: Path | str):
    _Classes = []

    for _Root, _Directories, _Files in os.walk(path_to_search):

        DIR_EXCLUSIONS = [r"__pycache__"]
        FILE_EXCLUSIONS = [r".*__init__\.py", r"^.*(?<!\.py)$"]
        Common.apply_exclusion_filter(_Directories, DIR_EXCLUSIONS)
        Common.apply_exclusion_filter(_Files, FILE_EXCLUSIONS)

        _Namespace = _Root.replace('/', '.').replace('\\', '.').lstrip(".")
        for _File in _Files:
            _Module = importlib.import_module(f"{_Namespace}.{_File[:-3]}", package=None)
            if _Module.__name__.lower().endswith(term.lower()):
                [_Classes.append((_Class))
                    for _, _Class
                    in inspect.getmembers(_Module, inspect.isclass)
                    if _Class.__module__ == _Module.__name__]

    return _Classes


def get_attributes_ending_with(term: str, path_to_search: Path | str):
    _Attributes = []

    for _Root, _Directories, _Files in os.walk(path_to_search):

        DIR_EXCLUSIONS = [r"__pycache__"]
        FILE_EXCLUSIONS = [r".*__init__\.py", r"^.*(?<!\.py)$"]
        Common.apply_exclusion_filter(_Directories, DIR_EXCLUSIONS)
        Common.apply_exclusion_filter(_Files, FILE_EXCLUSIONS)

        _Namespace = _Root.replace('/', '.').replace('\\', '.').lstrip(".")
        for _File in _Files:
            _Module = importlib.import_module(f"{_Namespace}.{_File[:-3]}", package=None)
            for _AttributeName, _AttributeValue in inspect.getmembers(_Module):
                if _AttributeName.lower().endswith(term.lower()):
                    _Attributes.append((_AttributeValue))

    return _Attributes


def try_parse_uuid(uuid_string: Any) -> UUID | None:
    try:
        return UUID(f"urn:uuid:{uuid_string}")
    except ValueError:
        return None


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
