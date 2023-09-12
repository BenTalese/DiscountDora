from abc import ABC, abstractmethod

class IPersistenceContext(ABC):
    @abstractmethod
    def add(self, entity):
        pass

    @abstractmethod
    async def save_changes_async(self): # FIXME: Only need self if requiring an instance...
        pass

    @abstractmethod
    def remove(self, entity):
        pass

    # @abstractmethod
    # def get_by_id(self, model_class, model_id):
    #     pass

    @abstractmethod
    def get_entities(self, entity_type):
        pass
