from abc import ABC, abstractmethod

from application.services.iquerybuilder import IQueryBuilder

class IPersistenceContext(ABC):
    @abstractmethod
    def add(self, entity) -> None: #TODO: Check all interfaces have returns defined
        pass

    @abstractmethod
    async def save_changes_async(self) -> None: # FIXME: Only need self if requiring an instance...
        pass

    @abstractmethod
    def remove(self, entity) -> None:
        pass

    # @abstractmethod
    # def get_by_id(self, model_class, model_id) -> ???:
    #     pass

    @abstractmethod
    def get_entities(self, entity_type) -> IQueryBuilder:
        pass
