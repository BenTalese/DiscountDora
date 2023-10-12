from abc import ABC
from typing import Callable

from application.infrastructure.bool_operation import BoolOperation


class IQueryBuilder(ABC):
    def any(self, condition: BoolOperation = None):
        return self

    def execute(self):
        pass

    def first(self, condition: BoolOperation = None):
        return self

    def first_by_id(self, *ids):
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        return self

    def first_by_id_or_none(self, *ids):
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        return self

    def first_or_none(self, condition: BoolOperation = None):
        return self

    def include(self, attribute_name: str):
       return self

    def project(self, func: Callable):
        return self

    def then_include(self, attribute_name: str):
        return self

    def where(self, condition: BoolOperation):
        return self
