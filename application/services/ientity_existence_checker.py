from abc import ABC, abstractmethod
from typing import List
from domain.entities.base_entity import EntityID

from domain.generics import TEntity


class IEntityExistenceChecker(ABC):

    @abstractmethod
    def does_entity_exist(self, entity_type: TEntity, entity_id: EntityID) -> bool:
        pass

    @abstractmethod
    def do_entities_exist(self, entity_type: TEntity, entity_ids: List[EntityID]) -> bool:
        pass
