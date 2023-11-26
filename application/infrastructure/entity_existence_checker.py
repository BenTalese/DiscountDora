from typing import List
from application.services.ientity_existence_checker import IEntityExistenceChecker
from application.services.ipersistence_context import IPersistenceContext
from domain.entities.base_entity import EntityID
from domain.generics import TEntity


class EntityExistenceChecker(IEntityExistenceChecker):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    def does_entity_exist(self, entity_type: TEntity, entity_id: EntityID) -> bool:
        return self.persistence_context \
            .get_entities(entity_type) \
            .first_by_id_or_none(entity_id) != None

    def do_entities_exist(self, entity_type: TEntity, entity_ids: List[EntityID]) -> bool:
        return all(self.does_entity_exist(entity_type, entity_id) for entity_id in entity_ids)
