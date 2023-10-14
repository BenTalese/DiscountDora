from abc import ABC, abstractmethod

from application.services.iquerybuilder import IQueryBuilder
from domain.generics import TEntity

class IPersistenceContext(ABC):
    @abstractmethod
    def add(self, entity: TEntity) -> None:
        pass

    @abstractmethod
    def get_entities(self, entity_type) -> IQueryBuilder[TEntity]:
        pass

    @abstractmethod
    def remove(self, entity: TEntity) -> None:
        pass

    @abstractmethod
    def save_changes_async(self: TEntity) -> None:
        pass
