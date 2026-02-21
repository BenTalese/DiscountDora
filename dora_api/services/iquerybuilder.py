from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List

from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.generics import TEntity
from dora_api.infrastructure.bool_operation import BoolOperation


class IQueryBuilder(ABC, Generic[TEntity]):
    @abstractmethod
    def all(self, condition: BoolOperation | str | None = None) -> List[TEntity]:
        '''
        `HINT/USAGE`
        first(Equal(input_port.merchant_id, (Merchant, nameof(Merchant.id))))
        '''
        pass

    @abstractmethod
    def by_id(self, entity_id: EntityID) -> TEntity | None:
        pass

    @abstractmethod
    def exists(self, entity_id: EntityID) -> bool:
        pass

    @abstractmethod
    def include(self, attribute_name: str) -> 'IQueryBuilder[TEntity]':
        return self

    @abstractmethod
    def one(self, condition: BoolOperation | str | None = None) -> TEntity | None:
        pass

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
