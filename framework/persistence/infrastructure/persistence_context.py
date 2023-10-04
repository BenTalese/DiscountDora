import ast
import inspect
import re
from enum import Enum
from typing import get_type_hints

import sqlalchemy
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.query import Query
from flask_sqlalchemy.session import Session
from sqlalchemy import Column, Select, select
from sqlalchemy.orm import (InstrumentedAttribute, joinedload, load_only,
                            subqueryload)
from varname import nameof

from application.dtos.stock_item_dto import get_stock_item_dto
from application.services.ipersistence_context import IPersistenceContext
from application.services.iquerybuilder import IQueryBuilder
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from framework.api.stock_items.view_models import (get_stock_item_next_thing,
                                                   get_stock_item_view_model)
from framework.persistence.infrastructure.seed import seed_initial_data_async

# TODO: Investigate getting IServiceProvider injected, do I need to register it against itself?

db = SQLAlchemy()

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
            # g = SqlAlchemyPersistenceContext().get_entities(StockItem).project(get_stock_item_dto).execute()
            g = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).execute()
            x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Equal(nameof(StockItem.name), "Test")).include(nameof(StockItem.location)).project(get_stock_item_dto).execute()
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).where(Equal(nameof(StockItem.name), "Test")).project(get_stock_item_dto).project(get_stock_item_view_model).project(get_stock_item_next_thing).execute()
            # x = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.location)).project(get_stock_item_dto).execute()
            v = 0
            await SqlAlchemyPersistenceContext().save_changes_async()

# TODO IMPORTANT!!! : I have a feeling once i change the model into the domain entity, it will stop tracking changes...
# ^ THIS MAY NOT BE AN ISSUE...test what happens on an update first before jumping to conclusions

# TODO: Find a home for this...
class SqlAlchemyQueryBuilder(IQueryBuilder):
    def __init__(self, session: sa_orm.scoped_session[Session], model_class, included_attributes = None):
        self._context = SqlAlchemyPersistenceContext._flask_app.app_context()
        with self._context:
            self.query: Select = select(model_class)
        # self.query: Select
        self.included_attributes = included_attributes or []
        self.included_model = None
        self.model = model_class
        self.session = session
        self.projections = []

    def any(self, condition = None):
        raise NotImplementedError()
        # with self._context:
        #     if condition:
        #         return self.query.filter(condition(self.model)).count() > 0
        #     else:
        #         return self.query.count() > 0

    def execute(self):
        with self._context:
            # if self.select_operations:
            #     # #model_attribute = getattr(self.model, attribute_name)
            #     # required_columns = [getattr(self.model, attr) for attr in self.select_mapping.values()]
            #     # for xg in required_columns:
            #     #     try:
            #     #         g = xg.comparator.entity.entity
            #     #     except:
            #     #         pass
            #     #     vv = 0
            #     # self.query = select(*required_columns)
            #     # x = self.session.execute(self.query).all()
            #     # attrs = {}
            #     # for row in x:
            #     #     columns = row._fields
            #     #     values = row._data
            #     #     col_vals = zip(columns, values)
            #     #     for ggg in col_vals:
            #     #         attrs[ggg[0]] = ggg[1]
            #     # ggh = self.model(**attrs).to_entity()
            #     # v = 0
            #     # #     for col in row:
            #     # #         for req_col in required_columns:
            #     # #         attrs[required_columns]
            #     # g = [self.model.to_entity(self.model(*row_result[0])) for row_result in x]
            #     # # g = [self.model.to_entity(self.model(*row_result[0])) for row_result in x]
            #     # row_results = self.session.execute(self.query.options(load_only(*required_columns))).all()
            #     x = 0
            # else:
            #     self.query = select(self.model)
                entities = [row_result[0].to_entity() for row_result in self.session.execute(self.query).all()]
                for projection in self.projections:
                    entities = [projection(entity) for entity in entities]
                return entities

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

    def include(self, attribute_name: str):
        attr = getattr(self.model, attribute_name)
        selected_model = self.get_model_from_attribute(attribute_name)
        selects = [self.model.id, self.model.name, selected_model.id, selected_model.description] # ALWAYS GET ID
        q = select(*selects).join(self.model.location)
        print(str(q))
        results = {}
        testthing = None
        for info, rslt in self.session.execute(q).all()[0]._key_to_index.items():
            results.setdefault(rslt, []).append(info)
            if type(info) == InstrumentedAttribute:
                testthing = info
            if issubclass(type(info), Column):
                v = 0
            if type(info) == str:
                v = 0


        row_results = self.session.execute(q).all()
        # TODO: Add to collection of created models, do not add duplicates
        # TODO: Link models together following relatonships
        models_from_rows = []
        for row_result in row_results:
            # # Get model types from row result
            # models_from_row = []

            # for metadata, column in column_metadata:
            #     if type(metadata) == InstrumentedAttribute and not metadata.parent.entity in models_from_row:
            #         models_from_row.append(metadata.parent.entity)

            # # Get list of model instances
            # model_instances = []
            # for model in models_from_row:
            #     model_instances.append(model())

            # 1. Collate metadata of columns
            metadata_by_column = {}
            for metadata, column in row_result._key_to_index.items():
                metadata_by_column.setdefault(column, []).append(metadata)

            # 2. Append actual data to metadata collection
            for column_name, column_data in row_result._mapping.items():
                for column in metadata_by_column.values():
                    if column[0] == column_name:
                        column.append(column_data)

            # 3. Collate model creation information
            models_to_be_created = {}
            for column in metadata_by_column.values():
                models_to_be_created.setdefault(column[1].parent.entity, {})[column[1].name] = column[3]

            # models_to_be_created = {}
            # for col_name, data in column_data.items():
            #     for col in metadata_by_column_index.values():
            #         if col[0] == col_name:
            #             models_to_be_created.setdefault(col[1].parent.entity, {})[col[1].name] = data

            # 4. Create models
            models_from_row = []
            for model, attrs in models_to_be_created.items():
                models_from_row.append(model(**attrs))

            for model in models_from_row:
                if not any(model.id == m.id for m in models_from_rows): # TODO: This assumes everything has one id...should compare entire object
                    models_from_rows.append(model)

            v = 0

        g = results.values()
        result_model = testthing.parent.entity
        result_entity = result_model().to_entity()
        t1 = testthing.prop
        t2 = testthing.property
        t3 = testthing.name





        model_attribute = getattr(self.model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model)
        joined_query.query = self.query.options(joinedload(model_attribute))
        joined_query.included_attributes = [model_attribute]
        joined_query.included_model = model_attribute.comparator.entity.entity
        return joined_query

    # TODO: Check source and dest types to ensure select is valid (e.g. not doing get_view_model with domain entity)
    # TODO: Test having more or less properties than expected
    def project(self, func):
        self.projections.append(func)
        assignments = []
        source_code = inspect.getsource(func)

        assignment_pattern = r'(\w+)\s*=\s*(.*?)\n'

        matches = re.findall(assignment_pattern, source_code)
        for match in matches:
            left_side, right_side = match
            assignments.append((left_side, right_side))
        v = 0
        # sources = set(func.__code__.co_names[1:])
        # destinations = set(func.__code__.co_consts[1])
        # select_mapping = {}
        # # self.select_operations[func] = attribute_mapping
        # # self.select_mapping = attribute_mapping

        # if not self.select_mapping:
        #     entity_type = get_type_hints(self.model.to_entity)['return']
        #     entity_attributes = set([attr for attr in dir(entity_type)
        #                          if not attr.startswith("__") and not attr.endswith("__")])
        #     self.select_operations.append(self.model.to_entity)

        #     sources = sources & entity_attributes
        #     attribute_mapping = zip(sources, destinations)


        #     for source, destination in attribute_mapping:
        #         if source in entity_attributes:
        #             select_mapping[destination] = source
        # else:
        #     for source, destination in attribute_mapping:
        #         if source in self.select_mapping.keys():
        #             select_mapping[destination] = self.select_mapping[source]
        #     # new_srcs = set(sources)
        #     # old_dests = set(self.current_select_mapping.keys())
        #     # common = new_srcs & old_dests
        #     # excluded = old_dests - sources
        #     # for val in self.current_select_mapping.values():
        #     #     if val in excluded:
        #     #         val = None

        # self.select_mapping = select_mapping
        return self

    def then_include(self, attribute_name: str):
        if not self.included_attributes:
            raise Exception("No relationship included.") #TODO: Better exception type
        model_attribute = getattr(self.included_model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model, self.included_attributes)
        joined_query.query = self.query.options(subqueryload(*self.included_attributes, model_attribute))
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

    def get_model_from_attribute(self, attribute_name: str):
        attr = getattr(self.model, attribute_name)
        return attr.comparator.entity.entity

# def get_assignments(func):
#     assignments = []
#     source_code = inspect.getsource(func)
#     assignment_pattern = r'(\w+)\s*=\s*(.*?)\n'

#     matches = re.findall(assignment_pattern, source_code)
#     for match in matches:
#         left_side, right_side = match
#         assignments.append((left_side.strip(), right_side.strip()))

#     return assignments

# def get_attribute_names(assignments, parameter_name):
#     attribute_names = {}

#     for left_side, right_side in assignments:
#         # Match expressions that reference the parameter (e.g., stock_item.name)
#         matches = re.findall(rf'{parameter_name}\.(\w+)', right_side)
#         if matches:
#             attribute_names[left_side] = matches[0]

#     return attribute_names

# assignments = get_assignments(get_stock_item_dto)
# attribute_names = get_attribute_names(assignments, parameter_name)


"""
Get left and right sides of assignment
Get a stripped down version of the right side of the assignment where it matches an attribute of the entity/model
Get the type hints for all attributes
For each stripped down right side string, check if the matching type hint is another entity/model and if so:
    Add that model (instrumented attribute) to the list of joins
    If there is an attribute match for the sub entity, add that to the selected columns
    Otherwise there is nothing trailing on the right side assignment (e.g. ".id") (COULD MAYBE USE .to_entity() AS THE SIGN?)
        Call this method again with this model to reach in further

Otherwise add to list of model attributes to select

If one of the attributes is a model/entity,

Going back...
<Create a model and assign the result set>
"""

v = 0
