from abc import ABC, abstractmethod

from application.services.iquerybuilder import IQueryBuilder

class IPersistenceContext(ABC):
    @abstractmethod
    def add(self, entity) -> None:
        pass

    @abstractmethod
    def get_entities(self, entity_type) -> IQueryBuilder:
        pass

    @abstractmethod
    def remove(self, entity) -> None:
        pass

    @abstractmethod
    def save_changes_async(self) -> None:
        pass
