import ast
import inspect
import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, get_origin, get_type_hints

import sqlalchemy
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.query import Query
from flask_sqlalchemy.session import Session
from sqlalchemy import Column, ForeignKey, Integer, Select, String, select
from sqlalchemy.orm import (InstrumentedAttribute, joinedload, load_only,
                            relationship, selectinload, subqueryload)
from sqlalchemy_utils import UUIDType
from varname import nameof

from application.dtos.stock_item_dto import get_stock_item_dto
from application.services.ipersistence_context import IPersistenceContext
from application.services.iquerybuilder import IQueryBuilder
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.test import Child, Parent
from framework.api.stock_items.view_models import (get_stock_item_next_thing,
                                                   get_stock_item_view_model)
from framework.persistence.infrastructure.seed import seed_initial_data_async

# TODO: Investigate getting IServiceProvider injected, do I need to register it against itself?

db = SQLAlchemy()

class TestModel(db.Model):
    __tablename__ = "Test"
    id1 = Column(
        String,
        primary_key=True,
        default="1")
    id2 = Column(
        Integer,
        primary_key=True,
        default=2)
    name = Column(String(255), default="Test")

class GreatGrandChildModel(db.Model):
    __tablename__ = "GreatGrandChild"
    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    name = Column(String(255))

class GrandChildModel(db.Model):
    __tablename__ = "GrandChild"
    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    name = Column(String(255))
    greatgrandchild = relationship("GreatGrandChildModel", uselist=False, lazy="noload")
    greatgrandchild_id = Column(UUIDType, ForeignKey("GreatGrandChild.id"))

class OtherGrandChildModel(db.Model):
    __tablename__ = "OtherGrandChild"
    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    name = Column(String(255))

class ChildModel(db.Model):
    __tablename__ = "Child"
    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    name = Column(String(255))
    grandchild = relationship("GrandChildModel", lazy="noload")
    grandchild_id = Column(UUIDType, ForeignKey("GrandChild.id"))
    parent_id = Column(UUIDType, ForeignKey("Parent.id"))

class OtherChildModel(db.Model):
    __tablename__ = "OtherChild"
    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    name = Column(String(255))
    grandchild = relationship("OtherGrandChildModel", lazy="noload")
    grandchild_id = Column(UUIDType, ForeignKey("OtherGrandChild.id"))
    parent_id = Column(UUIDType, ForeignKey("Parent.id"))

class ParentModel(db.Model):
    __tablename__ = "Parent"
    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    children = relationship("ChildModel", lazy="noload")
    otherchild = relationship("OtherChildModel", uselist=False, lazy="noload")

@dataclass
class ChildDto:
    dto_name: str

@dataclass
class ParentDto:
    dto_children: List[ChildDto]
    dto_children_names: List[str]

def get_child_dto(child: Child) -> ChildDto:
    return ChildDto(
        dto_name=child.name
    )

def get_parent_dto(parent: Parent) -> ParentDto:
    return ParentDto(
        dto_grandchild_names = [child.grandchild.name for child in parent.children],
        dto_children = [get_child_dto(child) for child in parent.children],
    )

class BoolOperation:
    def __init__(self, exp1, exp2):
        self.exp1 = exp1
        self.exp2 = exp2

    def sanitise(self, model):
        try:
            getattr(model, self.exp1)
            self.exp1 = f"self.model.{self.exp1}" #TODO: self.model. eeewwww
        except:
            if type(self.exp1) == str:
                self.exp1 = f"'{self.exp1}'"
        try:
            getattr(model, self.exp2)
            self.exp2 = f"self.model.{self.exp2}"
        except:
            if type(self.exp2) == str or type(self.exp2) == uuid.UUID:
                self.exp2 = f"'{self.exp2}'"

    def to_str(self, model):
        raise NotImplementedError()

class Equal(BoolOperation):
    def to_str(self, model):
        self.sanitise(model)
        return f"{self.exp1} == {self.exp2}"

class NotEqual(BoolOperation):
    def to_str(self, model):
        self.sanitise(model)
        return f"{self.exp1} != {self.exp2}"

class Greater(BoolOperation):
    def to_str(self, model):
        self.sanitise(model)
        return f"{self.exp1} > {self.exp2}"

class Less(BoolOperation):
    def to_str(self, model):
        self.sanitise(model)
        return f"{self.exp1} < {self.exp2}"

class GreaterOrEqual(BoolOperation):
    def to_str(self, model):
        self.sanitise(model)
        return f"{self.exp1} >= {self.exp2}"

class LessOrEqual(BoolOperation):
    def to_str(self, model):
        self.sanitise(model)
        return f"{self.exp1} <= {self.exp2}"

class Not(BoolOperation):
    def __init__(self, exp):
        self.exp = exp

    def to_str(self, model):
        return f"(not {self.exp.to_str(model)})"

class And(BoolOperation):
    def to_str(self, model):
        return f"({self.exp1.to_str(model)} and {self.exp2.to_str(model)})"

class Or(BoolOperation):
    def to_str(self, model):
        return f"({self.exp1.to_str(model)} or {self.exp2.to_str(model)})"

class Xor(BoolOperation):
    def to_str(self, model):
        return f"({self.exp1.to_str(model)} ^ {self.exp2.to_str(model)})"

class SqlAlchemyPersistenceContext(IPersistenceContext):
    _flask_app: Flask
    _model_classes: dict

    # ---------------- IPersistenceContext Methods ----------------

    def add(self, entity):
        db.session.add(self.convert_to_model(entity))

    def get_entities(self, entity_type):
        model_class = self.get_model_class(entity_type)
        return SqlAlchemyQueryBuilder(db.session, model_class)

    def remove(self, entity):
        db.session.delete(self.convert_to_model(entity))

    async def save_changes_async(self):
        db.session.commit()
        # asyncio.get_event_loop().run_in_executor(None, db.session.commit())

    # end IPersistenceContext Methods

    #TODO: Use class for options instead of .get("some string")
    @classmethod # TODO: Class method?? cls for what? maybe make static instead
    async def initialise(cls, app: Flask):
        import framework.persistence.models  # Must make models visible to db.init_app()
        db.init_app(app)
        app.db = db # TODO: This seems like very bad practice
        SqlAlchemyPersistenceContext._flask_app = app
        SqlAlchemyPersistenceContext._model_classes = {
            mapper.class_.__name__: mapper.class_
            for mapper in db.Model.registry.mappers
        }
        # SqlAlchemyPersistenceContext.identity_map = {}
        with app.app_context():
            if app.config.get('DEBUG'): # TODO Options interface, abstract away how settings are stored (nah, should be in config file)
                db.drop_all()
                db.create_all()
                greatgrandchild = GreatGrandChildModel(name="TestGreatGrandChild")
                grandchild = GrandChildModel(name="TestGrandChild", greatgrandchild=greatgrandchild)
                child1 = ChildModel(name="TestChild1", grandchild=grandchild)
                child2 = ChildModel(name="TestChild2")
                othergrandchild = OtherGrandChildModel(name="TestOtherGrandChild")
                otherchild = OtherChildModel(name="OtherChild")
                parent = ParentModel(children=[child1, child2], otherchild=otherchild)
                db.session.add(greatgrandchild)
                db.session.add(grandchild)
                db.session.add(othergrandchild)
                db.session.add(otherchild)
                db.session.add(child1)
                db.session.add(child2)
                db.session.add(parent)
                db.session.add(TestModel())
                db.session.commit()
                Migrate().init_app(app, db) # TODO: Do i need a migrate here?...
                await seed_initial_data_async(SqlAlchemyPersistenceContext())
            else:
                db.create_all() #TODO: This doesn't handle migrations on existing tables
                Migrate().init_app(app, db) # TODO: Create, mirate, or both?

    def get_model_class(self, entity_type):
        for model_class in self._model_classes.items():
            if model_class[0].replace("Model", "") == entity_type.__name__:
                return model_class[1]
        raise Exception(f"Model not found for: {entity_type.__name__}") #TODO: Test this is a good message

    # FIXME (Potentially): If this ever gets too ugly, make "to_model" methods on each model
    def convert_to_model(self, entity):
        model_class = self.get_model_class(type(entity))
        model_data = vars(entity).copy()
        for attr_name, type_hint in get_type_hints(entity).items():
            if hasattr(type_hint, "__module__") and "entities" in type_hint.__module__ and model_data[attr_name]:
                model_data[attr_name + '_id'] = model_data[attr_name].id
                del model_data[attr_name]

        return model_class(**model_data)

    @staticmethod
    async def test(app):
        with app.app_context():
            # result = app.db.session.query(ListingModel).all()
            # g = result[0].bids[0].listing
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Equal(nameof(StockItem.name), "Testee")).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).any()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).first_by_id(2, "1")
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).first(Equal(nameof(StockItem.id), uuid.uuid4()))
            g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).execute()
            g = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).execute()
            g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).project(get_stock_item_view_model).project(get_stock_item_next_thing).execute()
            g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).project(get_stock_item_view_model).execute()
            x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Equal(nameof(StockItem.name), "Test")).include(nameof(StockItem.location)).project(get_stock_item_dto).execute()
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Equal(nameof(StockItem.name), "Test")).project(get_stock_item_dto).project(get_stock_item_view_model).project(get_stock_item_next_thing).execute()
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).project(get_stock_item_dto).execute()
            v = 0
            await SqlAlchemyPersistenceContext().save_changes_async()




# TODO IMPORTANT!!! : I have a feeling once i change the model into the domain entity, it will stop tracking changes...
# ^ THIS MAY NOT BE AN ISSUE...test what happens on an update first before jumping to conclusions

# TODO: Find a home for this...
class SqlAlchemyQueryBuilder(IQueryBuilder):
    ASSIGNMENT_PATTERN = re.compile(r'(\w+)\s*=\s*(.*?)\n')

    def __init__(self, session: sa_orm.scoped_session[Session], model_class):
        self._context = SqlAlchemyPersistenceContext._flask_app.app_context()
        with self._context:
            self.query: Select = select(model_class)
        self.included_attribute_path = ""
        self.included_model = None
        self.model = model_class
        self.session = session
        self.projections = []
        self.projection_mapping = {}
        self.join_paths = {}

    def any(self, condition: BoolOperation = None):
        with self._context:
            if condition:
                return self.where(condition).any()
            return len(self.session.execute(self.query).unique().all()) > 0

    def execute(self):
        with self._context:
            self.join_paths = self.get_join_statements()
            for join_path in self.join_paths.values():
                self.query = self.query.options(joinedload(*join_path))

            print() # TODO: Remove after testing finishes
            print('\033[93m' + str(self.query) + '\033[0m')
            row_results = self.session.execute(self.query).unique().all()

            if self.projection_mapping:                                     # This could be part of .project(), but if it was it would retranslate every project
                translated_select_tree = {}
                for select_source in self.projection_mapping.values():
                    self.translate_projection_source(
                        translated_select_tree,
                        select_source.split("."),
                        get_type_hints(self.model.to_entity)['return'])

                models_from_select = []
                for row_result in row_results:
                    model_from_select = self.model()
                    self.depth_first_traversal(row_result[0], translated_select_tree, model_from_select)
                    models_from_select.append(model_from_select)

                projected_results = [model.to_entity() for model in models_from_select]
                for projection in self.projections:
                    projected_results = [projection(result) for result in projected_results]

                return projected_results

            return [row_result[0].to_entity() for row_result in row_results]

    def first(self, condition: BoolOperation = None):
        with self._context:
            if condition:
                return self.where(condition).first()

            result = self.session.execute(self.query).unique().all()
            if result:
                return result[0][0].to_entity()

            raise Exception("Result set was empty.") # TODO: Better exception

    def first_by_id(self, *ids):
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        result = self.session.get(self.model, ids)
        if result:
            return result.to_entity()

        raise Exception("No entity matching the provided ID.") # TODO: Better exception

    def first_by_id_or_none(self, *ids):
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        return self.session.get(self.model, ids).to_entity()

    def first_or_none(self, condition: BoolOperation = None):
        with self._context:
            if condition:
                return self.where(condition).first_or_none()

            result = self.session.execute(self.query).unique().all()
            if result:
                return result[0][0].to_entity()

            return None

    def depth_first_traversal(self, model_from_row_result, select_structure, model_being_created):
        for attribute_name, child_attributes in select_structure.items():
            if not child_attributes:
                setattr(model_being_created, attribute_name, getattr(model_from_row_result, attribute_name))
            else:
                linked_model_from_row_result = getattr(model_from_row_result, attribute_name)
                if not linked_model_from_row_result:
                    continue
                if type(linked_model_from_row_result) == sqlalchemy.orm.collections.InstrumentedList:
                    child_models = []
                    for linked_model_from_list_result in linked_model_from_row_result:
                        linked_model = self.get_model_definition_from_attribute(type(model_being_created), attribute_name)()
                        self.depth_first_traversal(linked_model_from_list_result, child_attributes, linked_model)
                        child_models.append(linked_model)
                    setattr(model_being_created, attribute_name, child_models)
                else:
                    linked_model = self.get_model_definition_from_attribute(type(model_being_created), attribute_name)()
                    self.depth_first_traversal(linked_model_from_row_result, child_attributes, linked_model)
                    setattr(model_being_created, attribute_name, linked_model)

    def translate_projection_source(self, projection_tree: dict, attributes: List[str], entity):
        def merge_nested_dicts(dict1: dict, dict2: dict):
            for key, value in dict2.items():
                if key not in dict1:
                    dict1[key] = value
                else:
                    merge_nested_dicts(dict1[key], value)

        if len(attributes) == 0:
            return {}

        attribute_name = attributes[0]
        attribute_type = get_type_hints(entity)[attribute_name]
        if len(attributes) == 1 and attribute_name in get_type_hints(entity).keys() and self.is_entity(attribute_type):
            entity_attributes = { attribute: {} for attribute in get_type_hints(attribute_type).keys() }
            if attribute_name not in projection_tree:
                projection_tree[attribute_name] = entity_attributes
            else:
                merge_nested_dicts(projection_tree[attribute_name], entity_attributes)

        elif attribute_name in projection_tree:
            source_to_merge = {}
            source_to_merge[attribute_name] = self.translate_projection_source({}, attributes[1:], attribute_type)
            merge_nested_dicts(projection_tree, source_to_merge)

        else:
            projection_tree[attribute_name] = self.translate_projection_source({}, attributes[1:], attribute_type)

        return projection_tree

    # USEFUL MAYBE (THIS USES load_only ????):
    # q = select(*selects).join(self.model.location)
    # q = select(self.model).options(joinedload(self.model.location)) #OLD WAY
    # q = select(self.model).options(load_only(self.model.id), joinedload(self.model.location).load_only(selected_model.id)) #NEW WAY
    def include(self, attribute_name: str):
        if not hasattr(self.model, attribute_name):
            raise Exception(f"Attribute '{attribute_name}' not present on model '{self.model}'.") #TODO: Better exception type

        if not self.is_model(self.model, attribute_name):
            raise Exception("Attribute '{attribute_name}' is not valid for include operation.") #TODO: Better exception type

        attribute_to_join = getattr(self.model, attribute_name)
        if nameof(attribute_to_join) not in self.join_paths.keys():
            self.join_paths[str(attribute_to_join)] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = self.get_model_definition_from_attribute(self.model, attribute_name)
        return self

    def get_source_attribute_path(self, source_type, assignment_path_to_search: str):
        source_attributes = get_type_hints(source_type).items()
        for attribute_name, attribute_type in source_attributes:
            # If entity attribute in assignment, and no other attribute precedes this attribute (avoid 'other_entity.id' bug)
            pattern = r'(' + '|'.join(name for name, _ in source_attributes if name != attribute_name) + r')\.' + attribute_name
            potential_attributes = []
            for attribute in assignment_path_to_search.split("."): #TODO: There's gotta be regex for this...
                potential_attributes.extend(attribute.split())
            if attribute_name in potential_attributes and not re.search(pattern, assignment_path_to_search):
                if self.is_entity(attribute_type) and (child_attribute := self.get_source_attribute_path(attribute_type, assignment_path_to_search)):
                    return attribute_name + "." + child_attribute
                return attribute_name
        return ""

    def is_entity(self, attribute_type):
        if get_origin(attribute_type) == list:
            attribute_type = attribute_type.__args__[0]
        return hasattr(attribute_type, "__module__") and "entities" in attribute_type.__module__

    def project(self, func):
        self.projections.append(func)
        source_code = inspect.getsource(func)
        attribute_assignments = self.ASSIGNMENT_PATTERN.findall(source_code)
        projection_source_type = list(inspect.signature(func).parameters.values())[0].annotation

        if not self.projection_mapping:
            for assignment in attribute_assignments:
                dest, src_path = assignment
                src_path: str = src_path.replace("[", "").replace("]", "").replace(",", "")
                self.projection_mapping[dest] = self.get_source_attribute_path(projection_source_type, src_path)
        else:
            new_projection_mapping = {}
            for assignment in attribute_assignments:
                dest, src_path = assignment
                src_path: str = src_path.replace("[", "").replace("]", "").replace(",", "")

                potential_attributes = []
                for string in src_path.split("."):
                    potential_attributes.extend(string.split())

                for attribute_name in get_type_hints(projection_source_type).keys():
                    if attribute_name in potential_attributes:
                        new_projection_mapping[dest] = self.projection_mapping[attribute_name]
                        break
            self.projection_mapping = new_projection_mapping

        return self

    def get_join_statements(self):
        joins = {}
        for attribute_path in self.projection_mapping.values():
            attributes_in_path = attribute_path.split('.')
            attribute_path_to_join = []
            attribute_path_as_string = ""
            model_type = self.model
            while attributes_in_path:
                attribute_name = attributes_in_path.pop(0)
                if self.is_model(model_type, attribute_name):
                    attribute_path_to_join.append(getattr(model_type, attribute_name))
                    attribute_path_as_string = ''.join([attribute_path_as_string, str(getattr(model_type, attribute_name))])
                    if attribute_path_as_string not in joins:
                        joins[attribute_path_as_string] = attribute_path_to_join
                    model_type = self.get_model_definition_from_attribute(model_type, attribute_name)
                else:
                    break
        return joins

    def is_model(self, model_type, attribute_name):
        return hasattr(getattr(getattr(model_type, attribute_name), "comparator"), "entity")

    def then_include(self, attribute_name: str):
        if not self.included_model:
            raise Exception("No relationship included.") #TODO: Better exception type

        if not hasattr(self.included_model, attribute_name):
            raise Exception(f"Attribute '{attribute_name}' not present on model '{self.model}'.") #TODO: Better exception type

        if not self.is_model(self.included_model, attribute_name):
            raise Exception("Attribute '{attribute_name}' is not valid for include operation.") #TODO: Better exception type

        # NEED TO MAKE IT MORE LIKE get_join_statements
        attribute_to_join = getattr(self.included_model, attribute_name)
        if nameof(attribute_to_join) not in self.join_paths.keys():
            self.join_paths[str(attribute_to_join)] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = self.get_model_definition_from_attribute(self.model, attribute_name)
        return self

        model_attribute = getattr(self.included_model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model, self.included_attributes)
        joined_query.query = self.query.options(selectinload(*self.included_attributes, model_attribute))
        joined_query.included_attributes.append(model_attribute)
        joined_query.included_model = model_attribute.comparator.entity.entity
        return joined_query

    def where(self, condition: BoolOperation):
        if not isinstance(condition, BoolOperation):
            raise Exception(f"Only '{nameof(BoolOperation)}' type is supported for this operation.") # TODO: Better exception

        self.query = self.query.where(eval(condition.to_str(self.model)))
        return self

    def get_model_definition_from_attribute(self, model_type, attribute_name: str):
        try:
            return getattr(model_type, attribute_name).comparator.entity.entity
        except:
            return None
