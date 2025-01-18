from abc import ABC, abstractmethod

from application.services.iquerybuilder import IQueryBuilder
from domain.generics import TEntity

class IPersistenceContext(ABC):
    @abstractmethod
    def add(self, entity: TEntity) -> None:
        pass

    @abstractmethod
    def get_entities(self, entity_type: TEntity) -> IQueryBuilder[TEntity]:
        pass

    @abstractmethod
    def remove(self, entity: TEntity) -> None:
        pass

    @abstractmethod
    async def save_changes_async(self) -> None:
        pass

    @abstractmethod
    def update(self, entity: TEntity) -> None:
        pass
