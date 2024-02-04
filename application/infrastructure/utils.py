import importlib
import inspect
import os

from clapy import Common


def get_classes_ending_with(term: str, path_to_search: str):
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

def get_attributes_ending_with(term: str, path_to_search: str):
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
