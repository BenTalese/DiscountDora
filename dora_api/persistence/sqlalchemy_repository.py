import inspect
import os
import re
from typing import Any, Callable, Generic, List
from uuid import uuid4

from domain.entities.base_entity import EntityID
from domain.generics import TEntity
from flask import Flask
from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload
from varname import nameof

from application.infrastructure.bool_operation import BoolOperation, Equal
from application.services.iquerybuilder import IQueryBuilder
from application.services.irepository import IRepository
from dora_api.app import db
from dora_api.domain.exceptions import PersistenceError


class SqlAlchemyRepository(IRepository[TEntity], Generic[TEntity]):
    _flask_app: Flask
    _model_classes: dict

    '''
    # TODO: Instead of _model_classes, do this:
    def __init__(self, model_class: type[Model]):
        self.model_class = model_class

    Then in dependency container:
    container.register(IRepository[Merchant], lambda: SqlAlchemyRepository(MerchantModel))

    This may affect .include() and .then_include()
    '''

    # ---------------- Interface Methods ----------------

    def add(self, entity: TEntity):
        # TODO: Move this to startup and validate all models in one go
        if _UnconfiguredAttributes := self._get_entity_unconfigured_attributes(entity):
            raise PersistenceError(f'{type(entity).__name__} entity is not valid for saving. '
                                   + f'Attributes require configuration: {", ".join(_UnconfiguredAttributes)}.')
        if entity.id.value:
            raise PersistenceError("Entity already persisted.")

        entity.id = EntityID(uuid4())
        db.session.add(self._convert_to_model(entity))

    def get(self, entity_type: type[TEntity]):
        return SqlAlchemyQueryBuilder(self._get_model_type(entity_type))

    def remove(self, entity: TEntity):
        db.session.delete(self._convert_to_model(entity))

    # FIXME: dunno what to do about the async-ness of this (would need FastAPI)
    def save_changes(self):
        db.session.commit()

    def update(self, entity: TEntity):
        if _UnconfiguredAttributes := self._get_entity_unconfigured_attributes(entity):
            raise PersistenceError(f'{type(entity).__name__} entity is not valid for saving. '
                                   + f'Attributes require configuration: {", ".join(_UnconfiguredAttributes)}.')

        db.session.add(self._convert_to_model(entity))

    # end Interface Methods

    # TODO: Use class for options instead of .get("some string")
    # TODO: Test on start that all entity properties have been configured (do name match)

    def _convert_to_model(self, entity: TEntity):
        return self._get_model_type(type(entity)).from_entity(entity)

    def _get_entity_unconfigured_attributes(self, entity: TEntity):
        _ModelAttributes = self._get_model_type(type(entity)).__dict__.keys()
        _EntityAttributes = entity.__dict__.keys()

        return list(set(_EntityAttributes) - set(_ModelAttributes))

    def _get_model_type(self, entity_type):
        if entity_type in self._model_classes:
            return self._model_classes[entity_type]

        raise PersistenceError(f"Model not found for: {entity_type.__name__}")


class SqlAlchemyQueryBuilder(IQueryBuilder, Generic[TEntity]):
    def __init__(self, model_class):
        self._context = SqlAlchemyRepository._flask_app.app_context()
        with self._context:
            self.query: Select = select(model_class)
        self.model_class = model_class
        self.included_attribute_path = ""
        self.included_model = None
        self.join_paths = {}

    def any(self, condition: BoolOperation | str | None = None) -> bool:
        if condition:
            return self.where(condition).any()
        return db.session.execute(self.query.limit(1)).first() is not None

    def execute(self) -> List[Any]:
        with self._context:
            self.query = self.query.options(
                *(joinedload(join_path) for join_path in self.join_paths.values())
            )

            print('\033[34m' + '\n=== EXECUTING QUERY ===\n' + '\033[93m' + str(self.query) + '\033[0m')
            models_from_query_result = [row_result[0] for row_result in db.session.execute(self.query).unique().all()]

            # TODO: Verify whatever the fuck this was talking about.....
            # if self.projections:
            #     # WHY: This must be done to prevent model attributes emitting another query to the database upon access
            #     casted_models = []
            #     for model in models_from_query_result:
            #         casted_model = self.model()
            #         cast_to_new_model(model, self.projection_tree, casted_model)
            #         casted_models.append(casted_model)
            #     models_from_query_result = casted_models

            entities = [model.to_entity() for model in models_from_query_result]
            return entities

    def first(self, condition: BoolOperation | str | None = None) -> TEntity:
        if condition:
            return self.where(condition).first()

        if result := self.execute():
            return result[0]

        raise PersistenceError("Result set was empty.")

    def first_by_id(self, entity_id: EntityID) -> TEntity:
        if result := self.first_or_none(Equal(entity_id, (self.model_class.__entity__, "id"))):
            return result

        raise PersistenceError("No entity matching the provided ID.")

    def first_by_id_or_none(self, entity_id: EntityID) -> TEntity | None:
        return self.first_or_none(Equal(entity_id, (self.model_class.__entity__, "id")))

    def first_or_none(self, condition: BoolOperation | str | None = None) -> TEntity | None:
        if condition:
            return self.where(condition).first_or_none()

        if result := self.execute():
            return result[0]

        return None

    def include(self, attribute_name: str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not hasattr(self.model_class, attribute_name):
            raise PersistenceError(f"Attribute '{attribute_name}' not present on model '{self.model_class}'.")

        if not self._is_model_attribute(self.model_class, attribute_name):
            raise PersistenceError(f"Attribute '{attribute_name}' is not valid for include operation.")

        attribute_to_join = getattr(self.model_class, attribute_name)
        if nameof(attribute_to_join) not in self.join_paths.keys():
            self.join_paths[str(attribute_to_join)] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = self._get_model_type_from_attribute(self.model_class, attribute_name)
        return self

    def project(self, projection_method: Callable) -> List[Any]:
        return [projection_method(entity) for entity in self.execute()]

    # TODO: Maybe this'd be useful some day?
    # def select(self, *columns: ColumnElement[Any]) -> 'IQueryBuilder[TEntity]':
    #     self.query = self.query.with_only_columns(*columns)
    #     return self

    def then_include(self, attribute_name: str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not self.included_model:
            raise PersistenceError("No relationship included.")

        if not hasattr(self.included_model, attribute_name):
            raise PersistenceError(f"Attribute '{attribute_name}' not present on model '{self.model_class}'.")

        if not self._is_model_attribute(self.included_model, attribute_name):
            raise PersistenceError("Attribute '{attribute_name}' is not valid for include operation.")

        attribute_to_join = getattr(self.included_model, attribute_name)
        attribute_path = self.included_attribute_path + "." + nameof(attribute_to_join)
        if attribute_path not in self.join_paths.keys():
            self.join_paths[attribute_path] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = self._get_model_type_from_attribute(self.included_model, attribute_name)
        return self

    def where(self, condition: BoolOperation | str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not isinstance(condition, BoolOperation) and not isinstance(condition, str):
            raise PersistenceError(f"Only '{nameof(BoolOperation)}' and 'str' types are supported for this operation.")

        condition = str(condition)

        find_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        entities_in_condition = find_pattern.findall(condition)
        for entity_name in entities_in_condition:
            model_name = [model.__name__ for entity, model in SqlAlchemyRepository._model_classes.items()
                          if entity.__name__ == entity_name][0]
            replace_pattern = re.compile(rf'\[\[{re.escape(entity_name)}\]\]')
            condition = re.sub(replace_pattern, model_name, condition)

        context = {model_type.__name__: model_type for model_type in SqlAlchemyRepository._model_classes.values()}

        # Required for case insensitive comparisons
        from sqlalchemy import func
        context['func'] = func

        print('\033[35m' + f"TRANSLATED CONDITION: {condition}" + '\033[0m')
        self.query = self.query.where(eval(condition, context))
        return self

    def _is_model_attribute(self, model_type, attribute_name):
        return hasattr(getattr(getattr(model_type, attribute_name), "comparator"), "entity")

    def _get_model_type_from_attribute(self, model_type, attribute_name: str):
        if self._is_model_attribute(model_type, attribute_name):
            return getattr(model_type, attribute_name).comparator.entity.entity
        return None


def verify_all_models_imported():
    import dora_api.persistence.models as models_module
    _Files = os.listdir(os.path.dirname(models_module.__file__))
    _Files.remove('__pycache__')
    _Files.remove('__init__.py')
    _ModuleNames = [_File.rstrip(".py") for _File in _Files]
    _Imports = inspect.getsource(models_module)
    for _Name in _ModuleNames:
        if _Name not in _Imports:
            raise PersistenceError(f"Not all models have been imported. Missing module: {_Name}.")
