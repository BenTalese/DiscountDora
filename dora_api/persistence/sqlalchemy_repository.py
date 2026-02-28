import inspect
import os
import re
from collections import deque
from dataclasses import fields
from typing import Any, Callable, Generic, List, get_origin, get_type_hints
from uuid import UUID, uuid4

import sqlalchemy
from flask import Flask
from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload
from varname import nameof

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.exceptions import PersistenceError
from dora_api.domain.generics import TEntity
from dora_api.infrastructure.bool_operation import BoolOperation, Equal
from dora_api.services.iquerybuilder import IQueryBuilder

'''
Note to my future self: This is pure insanity doing persistence this way. Sure, nice separated clean domain models, but
at the cost of absolutely fighting the ORM. Likely lost a ton of functionality by doing this, and research via AI suggests
most python projects just conflate the domain and persistence models. Perfect example of C# brain-rot. This force a
more "layered" architecture. We have all "features" talking to a single repository object (because f**k splitting this out).

I've kept this project like this to prove yes it can be done, but also to demonstrate why it shouldn't be done.
'''


class SqlAlchemyRepository:
    _flask_app: Flask
    _model_classes_by_entity: dict = {
        mapper.class_.__entity__: mapper.class_
        for mapper in db.Model.registry.mappers  # type: ignore
    }

    def __init__(self):
        self._added_models = {}
        self._queried_models = {}

    def add(self, entity: TEntity) -> None:
        ''' TODO: Create "excluded/ignored" class so you can do
            some_attribute = Ignore() in the model which acts like
            EF Core .Ignore(). Would have to pop/remove that attribute
            off the instance being saved, probably here in this method.
        '''
        # TODO: Move this to startup and validate all models in one go
        # TODO: Test on start that all entity properties have been configured (do name match)
        if _UnconfiguredAttributes := self._get_entity_unconfigured_attributes(entity):
            raise PersistenceError(f'{type(entity).__name__} entity is not valid for saving. '
                                   + f'Attributes require configuration: {", ".join(_UnconfiguredAttributes)}.')

        if entity.id.value != UUID(int=0):
            raise PersistenceError("Entity already persisted.")

        entity.id = EntityID(uuid4())
        _Model = self._convert_to_model(entity)
        self._added_models[entity.id.value] = _Model
        db.session.add(_Model)

    def get(self, entity_type: type[TEntity]) -> IQueryBuilder[TEntity]:
        return SqlAlchemyQueryBuilder(self, self._get_model_type(entity_type))

    def remove(self, entity: TEntity):
        db.session.delete(self._convert_to_model(entity))

    # FIXME: dunno what to do about the async-ness of this (would need FastAPI)
    def save_changes(self):
        db.session.commit()
        self._added_models.clear()
        self._queried_models.clear()

    def update(self, entity: TEntity):
        # TODO: See above to-do for add()
        if _UnconfiguredAttributes := self._get_entity_unconfigured_attributes(entity):
            raise PersistenceError(f'{type(entity).__name__} entity is not valid for saving. '
                                   + f'Attributes require configuration: {", ".join(_UnconfiguredAttributes)}.')

        db.session.add(self._convert_to_model(entity))

    def _get_entity_unconfigured_attributes(self, entity: TEntity):
        _ModelAttributes = self._get_model_type(type(entity)).__dict__.keys()
        _EntityAttributes = {
            f.name: getattr(entity, f.name)
            for f in fields(entity)
        }
        return list(set(_EntityAttributes) - set(_ModelAttributes))

    def _get_model_type(self, entity_type):
        if entity_type in self._model_classes_by_entity:
            return self._model_classes_by_entity[entity_type]
        raise PersistenceError(f"Model not found for: {entity_type.__name__}")

    def _convert_to_model(self, entity: TEntity):
        def convert_to_model(entity_instance: TEntity):
            if entity_instance.id.value in self._added_models:
                return self._added_models[entity_instance.id.value]
            elif entity_instance.id.value in self._queried_models:
                return self._queried_models[entity_instance.id.value]
            else:
                self.add(entity_instance)
                return self._added_models[entity_instance.id.value]

        _Model = self._get_model_type(type(entity))()
        _Model.id = entity.id.value

        if entity.id.value in self._queried_models:
            _Model = self._queried_models[entity.id.value]

        if entity.id.value in self._added_models:
            _Model = self._added_models[entity.id.value]

        for attribute_name, value in {f.name: getattr(entity, f.name) for f in fields(entity)}.items():
            if attribute_name == "id":
                continue

            attribute_type = get_type_hints(entity)[attribute_name]

            _IsList = is_list(attribute_type)  # Get before stripping down args attribute below

            # Deal with optional typehint, e.g. "stock_location: StockLocation | None"
            if hasattr(attribute_type, "__args__"):
                attribute_type = attribute_type.__args__[0]

            if attribute_type in self._model_classes_by_entity and value:
                if _IsList:
                    converted_models = []
                    for entity_in_list in value:
                        converted_models.append(convert_to_model(entity_in_list))
                    setattr(_Model, attribute_name, converted_models)
                else:
                    setattr(_Model, attribute_name, convert_to_model(value))

            else:
                setattr(_Model, attribute_name, value)

        return _Model


class SqlAlchemyQueryBuilder(IQueryBuilder[TEntity], Generic[TEntity]):
    def __init__(self, repository: SqlAlchemyRepository, model_class):
        self._context = repository._flask_app.app_context()
        with self._context:
            self.query: Select = select(model_class)
        self.included_attribute_path = ""
        self.included_model = None
        self.join_paths = {}
        self.model_class = model_class
        self.repository = repository

    # ---------------- IQueryBuilder Methods ----------------

    def all(self, condition: BoolOperation | str | None = None) -> List[TEntity]:
        if condition:
            return self.where(condition).all()
        return self._execute()

    def by_id(self, entity_id: EntityID) -> TEntity | None:
        return self.one(Equal(entity_id, (self.model_class.__entity__, "id")))

    def exists(self, entity_id: EntityID) -> bool:
        return self.by_id(entity_id) is not None

    def include(self, attribute_name: str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not hasattr(self.model_class, attribute_name):
            raise PersistenceError(f"Attribute '{attribute_name}' not present on model '{self.model_class}'.")

        if not is_model_attribute(self.model_class, attribute_name):
            raise PersistenceError(f"Attribute '{attribute_name}' is not valid for include operation.")

        attribute_to_join = getattr(self.model_class, attribute_name)
        if nameof(attribute_to_join) not in self.join_paths.keys():
            self.join_paths[str(attribute_to_join)] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = get_model_type_from_attribute(self.model_class, attribute_name)
        return self

    def one(self, condition: BoolOperation | str | None = None) -> TEntity | None:
        _Query = self.where(condition) if condition else self
        _Result = _Query._execute()
        return _Result[0] if _Result else None

    def project(self, projection_method: Callable) -> List[Any]:
        _Results = self._execute()
        return [projection_method(entity) for entity in _Results]

    # TODO: Maybe this'd be useful some day?
    # def select(self, *columns: ColumnElement[Any]) -> 'IQueryBuilder[TEntity]':
    #     self.query = self.query.with_only_columns(*columns)
    #     return self

    def then_include(self, attribute_name: str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not self.included_model:
            raise PersistenceError("No relationship included.")

        if not hasattr(self.included_model, attribute_name):
            raise PersistenceError(f"Attribute '{attribute_name}' not present on model '{self.model_class}'.")

        if not is_model_attribute(self.included_model, attribute_name):
            raise PersistenceError("Attribute '{attribute_name}' is not valid for include operation.")

        attribute_to_join = getattr(self.included_model, attribute_name)
        attribute_path = self.included_attribute_path + "." + nameof(attribute_to_join)
        if attribute_path not in self.join_paths.keys():
            self.join_paths[attribute_path] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = get_model_type_from_attribute(self.included_model, attribute_name)
        return self

    def where(self, condition: BoolOperation | str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not isinstance(condition, BoolOperation) and not isinstance(condition, str):
            raise PersistenceError(f"Only '{nameof(BoolOperation)}' and 'str' types are supported for this operation.")

        condition = str(condition)

        find_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        entities_in_condition = find_pattern.findall(condition)
        for entity_name in entities_in_condition:
            model_name = [model.__name__ for entity, model in self.repository._model_classes_by_entity.items()
                          if entity.__name__ == entity_name][0]
            replace_pattern = re.compile(rf'\[\[{re.escape(entity_name)}\]\]')
            condition = re.sub(replace_pattern, model_name, condition)

        context = {model_type.__name__: model_type for model_type in self.repository._model_classes_by_entity.values()}

        # Required for case insensitive comparisons
        from sqlalchemy import func
        context['func'] = func

        print('\033[35m' + f"TRANSLATED CONDITION: {condition}" + '\033[0m')
        self.query = self.query.where(eval(condition, context))
        return self

    # end IQueryBuilder Methods

    def _execute(self) -> List[Any]:
        with self._context:
            # TODO: joinedload? Is this correct for every load? There's other methods available
            for join_path in self.join_paths.values():
                self.query = self.query.options(joinedload(*join_path))

            print('\033[34m' + '\n=== EXECUTING QUERY ===\n' + '\033[93m' + str(self.query) + '\033[0m')

            models_from_query_result = [row_result[0] for row_result in db.session.execute(self.query).unique().all()]
            self._track_queried_models(models_from_query_result)
            entities = [model.to_entity() for model in models_from_query_result]
            return entities

    def _track_queried_models(self, models_from_query):
        model_queue = deque(models_from_query)

        while model_queue:
            current_model = model_queue.popleft()
            self.repository._queried_models[current_model.id] = current_model

            for attribute_value in vars(current_model).values():
                if is_model_list(attribute_value) and is_model(attribute_value):
                    [model_queue.append(model) for model in attribute_value]
                elif is_model(attribute_value):
                    model_queue.append(attribute_value)


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


def is_list(attribute_type):
    return get_origin(attribute_type) == list


def is_model_attribute(model_type, attribute_name):
    return hasattr(getattr(getattr(model_type, attribute_name), "comparator"), "entity")


def is_model_list(value):
    return type(value) is sqlalchemy.orm.collections.InstrumentedList


def is_model(value):
    if is_model_list(value) and value:
        value = value[0]
    return hasattr(type(value), "__module__") and "models" in type(value).__module__


def get_model_type_from_attribute(model_type, attribute_name: str):
    if is_model_attribute(model_type, attribute_name):
        return getattr(model_type, attribute_name).comparator.entity.entity
    return None
