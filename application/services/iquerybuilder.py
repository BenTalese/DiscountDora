from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List

from application.infrastructure.bool_operation import BoolOperation
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.generics import TEntity


class IQueryBuilder(ABC, Generic[TEntity]):
    @abstractmethod
    def any(self, condition: BoolOperation | str | None = None) -> bool:
        pass

    @abstractmethod
    def execute(self) -> List[Any]:
        pass

    @abstractmethod
    def first(self, condition: BoolOperation | str | None = None) -> TEntity:
        '''
        `HINT/USAGE`
        first(Equal(input_port.merchant_id, (Merchant, nameof(Merchant.id))))
        '''
        pass

    @abstractmethod
    def first_by_id(self, entity_id: EntityID) -> TEntity:
        pass

    @abstractmethod
    def first_by_id_or_none(self, entity_id: EntityID) -> TEntity | None:
        pass

    @abstractmethod
    def first_or_none(self, condition: BoolOperation | str | None = None) -> TEntity | None:
        pass

    @abstractmethod
    def include(self, attribute_name: str) -> 'IQueryBuilder[TEntity]':
        return self

    @abstractmethod
    def project(self, projection_method: Callable) -> List[Any]:
        pass

    @abstractmethod
    def then_include(self, attribute_name: str) -> 'IQueryBuilder[TEntity]':
        return self

    @abstractmethod
    def where(self, condition: BoolOperation | str) -> 'IQueryBuilder[TEntity]':
        '''
        `HINT/USAGE`
        where(Not(Equal((StockItem, nameof(StockItem.name)), "Test")))
        '''
        return self
