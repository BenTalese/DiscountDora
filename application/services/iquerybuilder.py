from abc import ABC
from typing import Any, Callable, Generic, List, Type

from application.infrastructure.bool_operation import BoolOperation
from domain.generics import TEntity


class IQueryBuilder(ABC, Generic[TEntity]):
    def any(self, condition: BoolOperation = None) -> bool:
        pass

    def execute(self) -> List[Any]:
        pass

    def first(self, condition: BoolOperation = None) -> TEntity:
        pass

    def first_by_id(self, *entity_ids) -> TEntity:
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        pass

    def first_by_id_or_none(self, *entity_ids) -> TEntity | None:
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        pass

    def first_or_none(self, condition: BoolOperation = None) -> TEntity | None:
        pass

    def include(self, attribute_name: str) -> Type['IQueryBuilder[TEntity]']:
        return self

    def project(self, method_of_projection: Callable) -> Type['IQueryBuilder[TEntity]']:
        return self

    def then_include(self, attribute_name: str) -> Type['IQueryBuilder[TEntity]']:
        return self

    def where(self, condition: BoolOperation) -> Type['IQueryBuilder[TEntity]']:
        '''
        `HINT/USAGE`
        where(Not(Equal((StockItem, nameof(StockItem.name)), "Test")))
        '''
        return self
