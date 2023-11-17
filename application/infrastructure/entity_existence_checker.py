from typing import List, Tuple
from application.services.ientity_existence_checker import IEntityExistenceChecker
from application.services.ipersistence_context import IPersistenceContext
from domain.entities.base_entity import EntityID
from domain.generics import TEntity


class EntityExistenceChecker(IEntityExistenceChecker):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    def does_entity_exist(self, entity_type: TEntity, *entity_ids: Tuple[EntityID]) -> bool:
        return self.persistence_context \
            .get_entities(entity_type) \
            .first_by_id_or_none(*entity_ids) != None

    def do_entities_exist(self, entities: List[TEntity]) -> bool:
        return all(self.does_entity_exist(entity) for entity in entities)
