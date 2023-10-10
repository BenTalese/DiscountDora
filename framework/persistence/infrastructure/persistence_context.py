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
from sqlalchemy import Column, ForeignKey, Select, String, select
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
            self.exp1 = f"self.model.{self.exp1}"
        except:
            if type(self.exp1) == str:
                self.exp1 = f"'{self.exp1}'"
        try:
            getattr(model, self.exp2)
            self.exp2 = f"self.model.{self.exp2}"
        except:
            if type(self.exp2) == str:
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
    def __init__(self, session: sa_orm.scoped_session[Session], model_class):
        self._context = SqlAlchemyPersistenceContext._flask_app.app_context()
        with self._context:
            self.query: Select = select(model_class)
        self.included_attribute_path = ""
        self.included_model = None
        self.model = model_class
        self.session = session
        self.projections = []
        self.select_mapping = {}
        self.join_paths = {}

    def any(self, condition = None):
        raise NotImplementedError()
        # with self._context:
        #     if condition:
        #         return self.query.filter(condition(self.model)).count() > 0
        #     else:
        #         return self.query.count() > 0

    def execute(self):
        with self._context:
            for join_path in self.join_paths.values():
                self.query = self.query.options(joinedload(*join_path))
            print()
            print(str(self.query))
            row_results = self.session.execute(self.query).unique().all()
            translated_select_tree = {}
            if self.select_mapping:                                     # This could be part of .project(), but if it was it would retranslate every project
                for select_source in self.select_mapping.values():
                    entity_type = get_type_hints(self.model.to_entity)['return']
                    self.create_nested_dict(select_source, translated_select_tree, entity_type)

            if translated_select_tree:
                models_from_select = []

                for row_result in row_results:
                    result_instance = row_result[0]
                    model_from_select = self.model()
                    self.depth_first_traversal(result_instance, translated_select_tree, model_from_select)
                    models_from_select.append(model_from_select)

                projected_results = [model.to_entity() for model in models_from_select]
                for projection in self.projections:
                    projected_results = [projection(result) for result in projected_results]

                return projected_results


            return [row_result[0].to_entity() for row_result in row_results]

    #TODO: define a select, and use in mapper so it actually trims down the result set

    def first(self, condition = None):
        raise NotImplementedError()
        # with self._context:
        #     if condition:
        #         return self.where(condition).first()
        #     return self.query.one().to_entity()

    def first_by_id(self, *ids):
        raise NotImplementedError()
        # result = self.session.get(*ids) # TODO: Wait how does this work? query is based on model, but this is based on what...?
        # if result:
        #     return result.to_entity()
        # else:
        #     raise Exception("Sequence contains no elements.") #TODO: Contains no elements, or not found...?

    def first_or_none(self, condition = None):
        raise NotImplementedError()
        # with self._context:
        #     if condition:
        #         result = self.where(condition).first_or_none()
        #         return result.to_entity() if result else None
        #     result = self.query.one_or_none().to_entity()
        #     return result.to_entity() if result else None

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

    def merge_nested_dicts(self, dict1, dict2):
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                self.merge_nested_dicts(dict1[key], value)
            else:
                dict1[key] = value

    def create_nested_dict(self, input_string, dict, entity):
        # Split the input string by periods to get a list of attribute names
        attributes = input_string.split('.') # TODO: Move this out to main calling code

        # Recursive function to build the nested structure
        def build_nested_dict(d, attrs):
            if len(attrs) == 0:
                return {}

            attr_name = attrs[0]
            if len(attrs) == 1 and attr_name in get_type_hints(entity).keys():
                attr_type = get_type_hints(entity)[attr_name]
                if get_origin(attr_type) == list:
                    attr_type = attr_type.__args__[0]
                if hasattr(attr_type, "__module__") and "entities" in attr_type.__module__:
                    x = {}
                    for attr in get_type_hints(attr_type).keys():
                        x[attr] = {}
                    if attr_name not in dict:
                        d[attr_name] = x
                    else:
                        self.merge_nested_dicts(dict, x)

            if attr_name not in dict:
                d[attr_name] = build_nested_dict({}, attrs[1:])
            else:
                conflict = {}
                conflict[attr_name] = build_nested_dict({}, attrs[1:])
                self.merge_nested_dicts(dict, conflict)
            return d

        # Call the recursive function to build the nested structure
        build_nested_dict(dict, attributes) # TODO: Move this out to main calling code

        return dict

    # USEFUL MAYBE (THIS USES load_only ????):
    # q = select(*selects).join(self.model.location)
    # q = select(self.model).options(joinedload(self.model.location)) #OLD WAY
    # q = select(self.model).options(load_only(self.model.id), joinedload(self.model.location).load_only(selected_model.id)) #NEW WAY
    # testparentchild = select(ParentModel).options(selectinload(ParentModel.children)) # USE SELECTINLOAD FOR EVERYTHING
    def include(self, attribute_name: str):
        if not hasattr(self.model, attribute_name):
            raise Exception(f"Attribute '{attribute_name}' not present on model '{self.model}'.")

        if not self.is_model(self.model, attribute_name):
            raise Exception("This property is not valid for include.")

        attribute_to_join = getattr(self.model, attribute_name)
        if nameof(attribute_to_join) not in self.join_paths.keys():
            self.join_paths[str(attribute_to_join)] = [attribute_to_join]

        self.included_attribute_path = nameof(attribute_to_join)
        self.included_model = self.get_model_definition_from_attribute(self.model, attribute_name)
        return self

    def get_assignment_source_attributes(self, source_type, string_to_search: str):
        source_attributes = get_type_hints(source_type).items()
        for attr_name, attr_type in source_attributes:
            # If entity attribute in assignment, and no other attribute precedes this attribute (avoid 'other_entity.id' bug)
            pattern = r'(' + '|'.join(name for name, _ in source_attributes if name != attr_name) + r')\.' + attr_name
            potential_attributes = []
            for string in string_to_search.split("."):
                potential_attributes.extend(string.split())
            if attr_name in potential_attributes and not re.search(pattern, string_to_search):
                if get_origin(attr_type) == list:
                    attr_type = attr_type.__args__[0]
                if hasattr(attr_type, "__module__") and "entities" in attr_type.__module__:
                    child_attr = self.get_assignment_source_attributes(attr_type, string_to_search)
                    if child_attr:
                        return attr_name + "." + child_attr
                    return attr_name
                else:
                    return attr_name
        return ""

    # TODO: Check source and dest types to ensure select is valid (e.g. not doing get_view_model with domain entity)
    def project(self, func):
        self.projections.append(func)
        assignment_pattern = r'(\w+)\s*=\s*(.*?)\n' # Compile regex?

        # FIXME: Can only use joinedload for my design, selectinload no work ( ; n;)... might still be fine for non-projection...maybe not, check sql str

        # x = select(ParentModel) \
        #     .options(joinedload(ParentModel.children)) \
        #     .options(joinedload(ParentModel.children, ChildModel.grandchild)) \
        #     .options(joinedload(ParentModel.children, ChildModel.grandchild, GrandChildModel.greatgrandchild))
        # print(str(x))
        # b = self.session.execute(x).unique().all()[0]

        # stuff = [
        #     [ParentModel.children],
        #     [ParentModel.children, ChildModel.grandchild],
        #     [ParentModel.children, ChildModel.grandchild, GrandChildModel.greatgrandchild],
        #     [ParentModel.otherchild],
        #     [ParentModel.otherchild, OtherChildModel.grandchild]
        # ]
        # testuru = select(ParentModel)
        # for x in stuff:
        #     testuru = testuru.options(joinedload(*x))

        # testu = self.session.execute(testuru).unique().all()[0]

        # TODO: remove them from joins when projected away? currently just recalculates entire join structure

        if not self.select_mapping:
            source_code = inspect.getsource(func)
            assignments = re.findall(assignment_pattern, source_code)
            source_type = list(inspect.signature(func).parameters.values())[0].annotation
            for assignment in assignments:
                left_side, right_side = assignment
                right_side = right_side.replace("[", "").replace("]", "").replace(",", "")
                self.select_mapping[left_side] = self.get_assignment_source_attributes(source_type, right_side)
        else:
            source_code = inspect.getsource(func)
            assignments = re.findall(assignment_pattern, source_code)
            source_type = list(inspect.signature(func).parameters.values())[0].annotation
            new_select_mapping = {}
            for assignment in assignments:
                left_side, right_side = assignment
                right_side = right_side.replace("[", "").replace("]", "").replace(",", "")
                for attr_name, _ in get_type_hints(source_type).items():
                    potential_attributes = []
                    for string in right_side.split("."):
                        potential_attributes.extend(string.split())
                    if attr_name in potential_attributes:
                        new_select_mapping[left_side] = self.select_mapping[attr_name]
                        break
            self.select_mapping = new_select_mapping

        self.join_paths = self.get_join_statements() #TODO: This will recalculate every projection...good? bad? idk...

        return self

    def get_join_statements(self):
        joins = {}
        for attribute_path in self.select_mapping.values():
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
        if not self.included_attributes:
            raise Exception("No relationship included.") #TODO: Better exception type
        model_attribute = getattr(self.included_model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model, self.included_attributes)
        joined_query.query = self.query.options(selectinload(*self.included_attributes, model_attribute))
        joined_query.included_attributes.append(model_attribute)
        joined_query.included_model = model_attribute.comparator.entity.entity
        return joined_query

    def where(self, condition: BoolOperation):
        # g = sqlalchemy.sql.Select.filter
        # lam = lambda x: str(x.name == "ggg")
        # x = lam(self.model)
        if not isinstance(condition, BoolOperation):
            raise Exception("You picked the wrong type, fool!")

        sql = condition.to_str(self.model)
        # stmt = select(self.model).where(eval(sql))
        # result = self.session.execute(stmt).all()
        v = 0
        filtered_query = SqlAlchemyQueryBuilder(self.session, self.model) # TODO: Look into not doing this and keeping the same instance for simplicity
        def append_dis():
            filtered_query.query = self.query.where(eval(sql))
        self.query_operations.append(append_dis)
        # if type(condition) == Equal:
        #     attr = getattr(self.model, condition.operand_one)
        #     stmt = select(self.model).where(attr == condition.operand_two)
        #     result = self.session.execute(stmt).all()
        #     v = 0
        # self.query = self.query.filter(condition(self.model))
        # # TODO: I doubt this will work, probably need to do something like this:

        # # def evaluate_expression(expression):
        # #     try:
        # #         result = eval(expression)
        # #         return result
        # #     except Exception as e:
        # #         return f"Error: {e}"

        # # def main():
        # #     expression = "x == 5"
        # #     result = evaluate_expression(expression)
        # #     print(f"Result of expression '{expression}': {result}")

        # # if __name__ == "__main__":
        # #     main()

        return filtered_query

    def get_model_definition_from_attribute(self, model_type, attribute_name: str):
        try:
            return getattr(model_type, attribute_name).comparator.entity.entity
        except:
            return None
