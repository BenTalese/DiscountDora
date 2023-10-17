import inspect
import os
import re
import uuid
from collections import deque
from typing import Any, Generic, List, Type, get_origin, get_type_hints

import sqlalchemy
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.session import Session
from sqlalchemy import (Column, ForeignKey, Integer, Select, String, Table,
                        select)
from sqlalchemy.orm import joinedload, load_only, relationship
from varname import nameof

from application.dtos.stock_item_dto import get_stock_item_dto
from application.infrastructure.bool_operation import BoolOperation, Equal, Not
from application.services.ipersistence_context import IPersistenceContext
from application.services.iquerybuilder import IQueryBuilder
from domain.entities.base_entity import EntityID
from domain.entities.shopping_list import ShoppingList
from domain.entities.stock_item import StockItem
from domain.generics import TEntity
from framework.api.stock_items.view_models import get_stock_item_view_model
from framework.persistence.infrastructure.persistence_helper_methods import (
    cast_to_new_model, get_model_type_from_attribute,
    get_source_attribute_path, is_entity, is_list, is_model,
    is_model_attribute, is_model_list, translate_projection_source)
from framework.persistence.infrastructure.seed import seed_initial_data_async

# TODO: Investigate getting IServiceProvider injected, do I need to register it against itself?
# TODO IMPORTANT!!! : I have a feeling once i change the model into the domain entity, it will stop tracking changes...
# ^ THIS MAY NOT BE AN ISSUE...test what happens on an update first before jumping to conclusions

db = SQLAlchemy()

# class TestModel(db.Model):
#     __entity__ = None
#     __tablename__ = "Test"
#     id = Column(
#         Integer,
#         primary_key=True)
#     name = Column(String(255))

# class ChildModel(db.Model):
#     __entity__ = None
#     __tablename__ = "Child"
#     id = Column(
#         Integer,
#         primary_key=True)
#     name = Column(String(255))
#     parent_id = Column(Integer, ForeignKey("Parent.id"))

# class Child:
#     id: int = None
#     name: str = None

# class Parent:
#     id: int = None
#     name: str = None
#     child: List[Child] = None

# class ParentModel(db.Model):
#     __entity__ = None
#     __tablename__ = "Parent"
#     id = Column(
#         Integer,
#         primary_key=True)
#     name = Column(String(255))
#     child = relationship("ChildModel", lazy="noload", cascade="all, delete-orphan")

# student_course_association = db.Table(
#     'student_course_association',
#     db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
#     db.Column('course_id', db.Integer, db.ForeignKey('courses.id'))
# )

# class Student(db.Model):
#     __entity__ = None
#     __tablename__ = 'students'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255))
#     courses = db.relationship('Course', secondary='student_course_association', back_populates='students')

# class Course(db.Model):
#     __entity__ = None
#     __tablename__ = 'courses'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255))
#     students = db.relationship('Student', secondary='student_course_association', back_populates='courses')


class SqlAlchemyPersistenceContext(IPersistenceContext):
    _flask_app: Flask
    _model_classes: dict
    _added_models = {}
    _queried_models = {}

    # ---------------- IPersistenceContext Methods ----------------

    def _convert_to_model(self, entity: TEntity):
        def convert_to_model(entity_instance):
            # If already already added within this transaction, get same instance
            if entity_instance.id and entity_instance.id.value in self._added_models:
                return self._added_models[entity_instance.id.value]
            # If already persisted entity
            elif entity_instance.id:
                return self._queried_models[entity_instance.id.value]
            # If new entity, not yet added
            else:
                self.add(entity_instance)
                return self._added_models[entity_instance.id.value]

        model = self._get_model_type(type(entity))()
        model.id = entity.id.value

        if entity.id.value in self._queried_models:
            model = self._queried_models[entity.id.value]

        if entity.id.value in self._added_models:
            model = self._added_models[entity.id.value]

        for attribute_name, value in entity.__dict__.items():
            if attribute_name == "id":
                continue

            attribute_type = get_type_hints(entity)[attribute_name]
            if is_entity(attribute_type) and value:
                if is_list(attribute_type):
                    converted_models = []
                    for entity_in_list in value:
                        converted_models.append(convert_to_model(entity_in_list))
                    setattr(model, attribute_name, converted_models)
                else:
                    setattr(model, attribute_name, convert_to_model(value))

            else:
                setattr(model, attribute_name, value)

        return model

    def add(self, entity: TEntity):
        # parent = ParentModel(id=1, name="TestParent")
        # child1 = ChildModel(id=1, name="TestChild1")
        # child2 = ChildModel(id=2, name="TestChild2")
        # parent.child = [child1, child2]
        # db.session.add(parent)
        # db.session.commit()
        # # db.session.expunge_all()
        # self._queried_models[parent.id] = db.session.query(ParentModel).options(joinedload(ParentModel.child)).all()[0]
        # parent_update = Parent()
        # parent_update.id = 1
        # parent_update.name = "THIS IS SHIT"
        # child2 = ChildModel(id=2, name="TestChild2")
        # child3 = ChildModel(id=3, name="AAHHH")
        # parent_update.child = [child2, child3]
        # existing_parent = self._queried_models[parent_update.id]
        # existing_data = vars(existing_parent)
        # for attr, val in parent_update.__dict__.items():
        #     if val != existing_data[attr]:
        #         setattr(existing_parent, attr, val)

        # db.session.commit()


        # student1 = Student(id=1, name="Bob")
        # student2 = Student(id=2, name="Bill")
        # course = Course(id=5, name="Science")
        # course.students = [student1, student2]
        # db.session.add(course)
        # db.session.commit()
        # self._queried_models[course.id] = db.session.query(Course).options(joinedload(Course.students)).all()[0]
        # self._queried_models[student1.id] = db.session.query(Student).options(joinedload(Student.courses)).all()[0]
        # self._queried_models[student2.id] = db.session.query(Student).options(joinedload(Student.courses)).all()[1]

        # student_update = { "id": 1, "name": "Bob", "courses": [] }
        # existing_student = self._queried_models[1]
        # existing_student_data = vars(existing_student)
        # for attr, val in student_update.items():
        #     if val != existing_student_data[attr]:
        #         setattr(existing_student, attr, val)

        # db.session.commit()


        if not entity.id:
            entity.id = EntityID(uuid.uuid4())

            model = self._convert_to_model(entity)

            self._added_models[entity.id.value] = model
            db.session.add(model)

    def get_entities(self, entity_type: TEntity):
        model_class = self._get_model_type(entity_type)
        return SqlAlchemyQueryBuilder(db.session, self, model_class)

    def remove(self, entity: TEntity):
        db.session.delete(self._convert_to_model(entity))

    # FIXME: dunno what to do about the async-ness of this
    # FIXME: technically it would be best if save_changes was separate to the
    # context, persisting is a framework concern, not an application concern
    # TODO: Find out if _queried_models should also be cleared here...me thinks maybe not
    async def save_changes_async(self):
        db.session.commit()
        self._added_models.clear()
        # asyncio.get_event_loop().run_in_executor(None, db.session.commit())

    def update(self, entity: TEntity):
        # model_to_update = self._queried_models[entity.id.value]
        # model_data = vars(model_to_update)
        # for attr, val in entity.__dict__.items():
        #     if attr == "id":
        #         continue

        #     attr_type = get_type_hints(entity)[attr]
        #     if val != model_data[attr] and not is_entity(attr_type):
        #         setattr(model_to_update, attr, val)

        #     if val != model_data[attr] and is_entity(attr_type):
        #         pass

        db.session.add(self._convert_to_model(entity))
        # db.session.merge(model_to_update) # TODO: The model is detached which I think makes this not work

    # end IPersistenceContext Methods

    #TODO: Use class for options instead of .get("some string")
    @classmethod # TODO: Class method?? cls for what? maybe make static instead
    async def initialise(cls, app: Flask):
        SqlAlchemyPersistenceContext._verify_all_models_imported()
        import framework.persistence.models  # Makes models visible to db.init_app()
        db.init_app(app)
        app.db = db # TODO: This seems like very bad practice
        SqlAlchemyPersistenceContext._flask_app = app
        SqlAlchemyPersistenceContext._model_classes = {
            mapper.class_.__entity__ : mapper.class_
            for mapper in db.Model.registry.mappers
        }
        # SqlAlchemyPersistenceContext.identity_map = {}
        with app.app_context():
            if app.config.get('DEBUG'): # TODO Options interface, abstract away how settings are stored (nah, should be in config file)
                db.drop_all()
                db.create_all()
                db.session.commit()
                Migrate().init_app(app, db) # TODO: Do i need a migrate here?...
                await seed_initial_data_async(SqlAlchemyPersistenceContext())
            else:
                db.create_all() #TODO: This doesn't handle migrations on existing tables
                Migrate().init_app(app, db) # TODO: Create, mirate, or both?

    def _get_model_type(self, entity_type):
        if entity_type in self._model_classes:
            return self._model_classes[entity_type]

        raise Exception(f"Model not found for: {entity_type.__name__}")

    @staticmethod
    def _verify_all_models_imported():
        import framework.persistence.models as models_module
        _Files = os.listdir(os.path.dirname(models_module.__file__))
        _Files.remove('__pycache__')
        _Files.remove('__init__.py')
        _ModuleNames = [_File.rstrip(".py") for _File in _Files]
        _Imports = inspect.getsource(models_module)
        for _Name in _ModuleNames:
            if _Name not in _Imports:
                raise Exception(f"Not all models have been imported. Missing module: {_Name}.")

    @staticmethod
    async def test(app):
        with app.app_context():
            # persistence = SqlAlchemyPersistenceContext()
            # to_remove: StockItem = SqlAlchemyPersistenceContext().get_entities(StockItem).first()
            # # might not work bc different instances of persistence
            # to_remove.name = "AHHHHH IT WORKS!"
            # SqlAlchemyPersistenceContext().update(to_remove)
            # things = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).project(get_stock_item_view_model).execute() # FIXME: Look into why execute is not recognised here
            to_update: ShoppingList = SqlAlchemyPersistenceContext().get_entities(ShoppingList).include("items").first()
            SqlAlchemyPersistenceContext().update(to_update)
            await SqlAlchemyPersistenceContext().save_changes_async()
            things = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).execute()
            x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Not(Equal((StockItem, nameof(StockItem.name)), "Test"))).execute()
            # result = app.db.session.query(ListingModel).all()
            # g = result[0].bids[0].listing
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Equal(nameof(StockItem.name), "Testee")).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).any()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).first_by_id(2, "1")
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).first(Equal(nameof(StockItem.id), uuid.uuid4()))
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Not(Equal((StockItem, nameof(StockItem.name)), "Test"))).include(nameof(StockItem.location)).project(get_stock_item_dto).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).project(get_stock_item_view_model).project(get_stock_item_next_thing).execute()
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).project(get_stock_item_view_model).execute()
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).project(get_stock_item_dto).execute()
            v = 0
            await SqlAlchemyPersistenceContext().save_changes_async()


#TODO: Put other regex up top if possible
class SqlAlchemyQueryBuilder(IQueryBuilder, Generic[TEntity]):
    ASSIGNMENT_PATTERN = re.compile(r'(\w+)\s*=\s*(.*?)\n')

    def __init__(self, session: sa_orm.scoped_session[Session], persistence_context: SqlAlchemyPersistenceContext, model_class):
        self._context = persistence_context._flask_app.app_context()
        with self._context:
            self.query: Select = select(model_class)
        self.included_attribute_path = ""
        self.included_model = None
        self.join_paths = {}
        self.model = model_class
        self.persistence_context = persistence_context
        self.projections = []
        self.projection_mapping = {}
        self.projection_tree = {}
        self.session = session

    # ---------------- IQueryBuilder Methods ----------------

    def any(self, condition: BoolOperation = None) -> bool:
        with self._context:
            if condition:
                return self.where(condition).any()
            return len(self.execute()) > 0

    def execute(self) -> List[Any]:
        with self._context:
            if self.projections:
                for select_source in self.projection_mapping.values():
                    translate_projection_source(
                        self.projection_tree,
                        select_source.split("."),
                        self.model.__entity__)

                self.join_paths = self._get_projection_joins()

            for join_path in self.join_paths.values():
                self.query = self.query.options(joinedload(*join_path))

            # TODO: SQLALCHEMY LOAD_ONLY() FOR PROJECTIONS
            # load_only_attributes = [attr for attr, tree in self.projection_tree.items() if not tree]
            # for attr in load_only_attributes:
            #     model_attr = getattr(self.model, attr)
            #     self.query = self.query.options(load_only(model_attr))

            print('\033[34m' + '\n=== EXECUTING QUERY ===\n' + '\033[93m' + str(self.query) + '\033[0m')
            if self.projections: print('\033[32m' + f'PROJECTION: {self.projection_tree}' + '\033[0m')

            models_from_query_result = [row_result[0] for row_result in self.session.execute(self.query).unique().all()]

            if self.projections:
                # WHY: This must be done to prevent model attributes emitting another query to the database upon access
                casted_models = []
                for model in models_from_query_result:
                    casted_model = self.model()
                    cast_to_new_model(model, self.projection_tree, casted_model)
                    casted_models.append(casted_model)
                models_from_query_result = casted_models

            self._track_queried_models(models_from_query_result)

            entities = [model.to_entity() for model in models_from_query_result]

            for projection in self.projections:
                entities = [projection(instance) for instance in entities]

            return entities

    def first(self, condition: BoolOperation = None) -> TEntity:
        if condition:
            return self.where(condition).first()

        if result:= self.execute():
            return result[0]

        raise Exception("Result set was empty.")

    def first_by_id(self, *entity_ids) -> TEntity:
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        ids = (id.value for id in entity_ids)
        if result:= self.session.get(self.model, *ids):
            self.persistence_context._queried_models[*ids] = result
            return result.to_entity()

        raise Exception("No entity matching the provided ID.")

    def first_by_id_or_none(self, *entity_ids) -> TEntity | None:
        '''
        `HINT/USAGE`
        Single id: first_by_id(1)
        Composite id style 1: first_by_id(1, 2) `Order must match order of column definitions`
        Composite id style 2: first_by_id({"id1": 1, "id2": 2})
        '''
        ids = (id.value for id in entity_ids)
        if result:= self.session.get(self.model, *ids):
            self.persistence_context._queried_models[*ids] = result
            return result.to_entity()
        return None

    def first_or_none(self, condition: BoolOperation = None) -> TEntity | None:
        if condition:
            return self.where(condition).first_or_none()

        if result:= self.execute():
            return result[0]

        return None

    def include(self, attribute_name: str) -> Type['SqlAlchemyQueryBuilder[TEntity]']:
        if not hasattr(self.model, attribute_name):
            raise Exception(f"Attribute '{attribute_name}' not present on model '{self.model}'.")

        if not is_model_attribute(self.model, attribute_name):
            raise Exception(f"Attribute '{attribute_name}' is not valid for include operation.")

        attribute_to_join = getattr(self.model, attribute_name)
        if nameof(attribute_to_join) not in self.join_paths.keys():
            self.join_paths[str(attribute_to_join)] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = get_model_type_from_attribute(self.model, attribute_name)
        return self

    def project(self, method_of_projection) -> Type['SqlAlchemyQueryBuilder[TEntity]']:
        self.projections.append(method_of_projection)
        source_code = inspect.getsource(method_of_projection)
        attribute_assignments = self.ASSIGNMENT_PATTERN.findall(source_code)
        projection_source_type = list(inspect.signature(method_of_projection).parameters.values())[0].annotation

        if not self.projection_mapping:
            for assignment in attribute_assignments:
                dest, src_path = assignment
                src_path: str = src_path.replace("[", "").replace("]", "").replace(",", "")
                self.projection_mapping[dest] = get_source_attribute_path(projection_source_type, src_path)
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

    def then_include(self, attribute_name: str) -> Type['SqlAlchemyQueryBuilder[TEntity]']:
        if not self.included_model:
            raise Exception("No relationship included.")

        if not hasattr(self.included_model, attribute_name):
            raise Exception(f"Attribute '{attribute_name}' not present on model '{self.model}'.")

        if not is_model_attribute(self.included_model, attribute_name):
            raise Exception("Attribute '{attribute_name}' is not valid for include operation.")

        attribute_to_join = getattr(self.included_model, attribute_name)
        attribute_path = self.included_attribute_path + "." + nameof(attribute_to_join)
        if attribute_path not in self.join_paths.keys():
            self.join_paths[attribute_path] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = get_model_type_from_attribute(self.included_model, attribute_name)
        return self

    def where(self, condition: BoolOperation) -> Type['SqlAlchemyQueryBuilder[TEntity]']:
        if not isinstance(condition, BoolOperation):
            raise Exception(f"Only '{nameof(BoolOperation)}' type is supported for this operation.")

        condition_code = str(condition)

        pattern = re.compile(r'\[\[([^\]]+)\]\]')
        entities_in_condition = pattern.findall(condition_code)
        for entity_name in entities_in_condition:
            model_name = [model.__name__ for entity, model in self.persistence_context._model_classes.items()
                          if entity.__name__ == entity_name][0]
            condition_code = re.sub(pattern, model_name, condition_code)

        context = { model_type.__name__: model_type for model_type in self.persistence_context._model_classes.values()}

        self.query = self.query.where(eval(condition_code, context))
        return self

    # end IQueryBuilder Methods

    # ---------------- QueryBuilder Helper Methods ----------------

    def _track_queried_models(self, models_from_query):
        model_queue = deque(models_from_query)

        while model_queue:
            current_model = model_queue.popleft()
            self.persistence_context._queried_models[current_model.get_key()] = current_model

            for attribute_value in vars(current_model).values():
                if is_model_list(attribute_value) and is_model(attribute_value):
                    [model_queue.append(model) for model in attribute_value]
                elif is_model(attribute_value):
                    model_queue.append(attribute_value)

    # FIXME: This needs to be rewritten based on projection_tree
    def _get_projection_joins(self):
        joins = {}
        for attribute_path in self.projection_mapping.values():
            attributes_in_path = attribute_path.split('.')
            attribute_path_to_join = []
            attribute_path_as_string = ""
            model_type = self.model
            while attributes_in_path:
                attribute_name = attributes_in_path.pop(0)
                if is_model_attribute(model_type, attribute_name):
                    attribute_path_to_join.append(getattr(model_type, attribute_name))
                    attribute_path_as_string = ''.join([attribute_path_as_string, str(getattr(model_type, attribute_name))])
                    if attribute_path_as_string not in joins:
                        joins[attribute_path_as_string] = attribute_path_to_join
                    model_type = get_model_type_from_attribute(model_type, attribute_name)
                else:
                    break
        return joins

    # end QueryBuilder Helper Methods
