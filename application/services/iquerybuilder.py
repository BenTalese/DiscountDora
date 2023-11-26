from abc import ABC
from typing import Any, Callable, Generic, List, Type

from application.infrastructure.bool_operation import BoolOperation
from domain.entities.base_entity import EntityID
from domain.generics import TEntity


class IQueryBuilder(ABC, Generic[TEntity]):
    def any(self, condition: BoolOperation | str = None) -> bool:
        pass

    def execute(self) -> List[Any]:
        pass

    def first(self, condition: BoolOperation | str = None) -> TEntity:
        '''
        `HINT/USAGE`
        first(Equal(input_port.merchant_id, (Merchant, nameof(Merchant.id))))
        '''
        pass

    def first_by_id(self, entity_id: EntityID) -> TEntity:
        pass

    def first_by_id_or_none(self, entity_id: EntityID) -> TEntity | None:
        pass

    def first_or_none(self, condition: BoolOperation | str = None) -> TEntity | None:
        pass

    def include(self, attribute_name: str) -> Type['IQueryBuilder[TEntity]']:
        return self

    def project(self, method_of_projection: Callable) -> Type['IQueryBuilder[TEntity]']:
        return self

    def then_include(self, attribute_name: str) -> Type['IQueryBuilder[TEntity]']:
        return self

    def where(self, condition: BoolOperation | str) -> Type['IQueryBuilder[TEntity]']:
        '''
        `HINT/USAGE`
        where(Not(Equal((StockItem, nameof(StockItem.name)), "Test")))
        '''
        return self
