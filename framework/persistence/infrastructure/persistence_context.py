import ast
import inspect
from enum import Enum
from typing import get_type_hints

import sqlalchemy
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.query import Query
from flask_sqlalchemy.session import Session
from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload, load_only, subqueryload
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
        # with self._context:
        #     self.query: Select = select(model_class)
        self.query: Select
        self.included_attributes = included_attributes or []
        self.included_model = None
        self.model = model_class
        self.session = session
        self.select_operations = []
        self.select_mapping = {}
        self.selected_columns = set()
        self.query_operations = []

    def any(self, condition = None):
        raise NotImplementedError()
        # with self._context:
        #     if condition:
        #         return self.query.filter(condition(self.model)).count() > 0
        #     else:
        #         return self.query.count() > 0

    def execute(self):
        with self._context:
            if self.select_operations:
                #model_attribute = getattr(self.model, attribute_name)
                required_columns = [getattr(self.model, attr) for attr in self.select_mapping.values()]
                for xg in required_columns:
                    try:
                        g = xg.comparator.entity.entity
                    except:
                        pass
                    vv = 0
                self.query = select(*required_columns)
                x = self.session.execute(self.query).all()
                attrs = {}
                for row in x:
                    columns = row._fields
                    values = row._data
                    col_vals = zip(columns, values)
                    for ggg in col_vals:
                        attrs[ggg[0]] = ggg[1]
                ggh = self.model(**attrs).to_entity()
                v = 0
                #     for col in row:
                #         for req_col in required_columns:
                #         attrs[required_columns]
                g = [self.model.to_entity(self.model(*row_result[0])) for row_result in x]
                # g = [self.model.to_entity(self.model(*row_result[0])) for row_result in x]
                row_results = self.session.execute(self.query.options(load_only(*required_columns))).all()
                x = 0
            else:
                self.query = select(self.model)
                for operation in self.query_operations:
                    operation()
                return [row_result[0].to_entity() for row_result in self.session.execute(self.query).all()]

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

    # # https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html
    def include(self, attribute_name: str):
        model_attribute = getattr(self.model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model)
        joined_query.query = self.query.options(joinedload(model_attribute))
        joined_query.included_attributes = [model_attribute]
        joined_query.included_model = model_attribute.comparator.entity.entity
        return joined_query

    # TODO: Check source and dest types to ensure select is valid (e.g. not doing get_view_model with domain entity)
    # TODO: Test having more or less properties than expected
    def project(self, func):
        self.select_operations.append(func)
        sources = func.__code__.co_names[1:]
        destinations = func.__code__.co_consts[1]
        attribute_mapping = zip(sources, destinations)
        select_mapping = {}
        # self.select_operations[func] = attribute_mapping
        # self.select_mapping = attribute_mapping

        if not self.select_mapping:
            entity_type = get_type_hints(self.model.to_entity)['return']
            entity_attributes = [attr for attr in dir(entity_type)
                                 if not attr.startswith("__") and not attr.endswith("__")]
            self.select_operations.append(self.model.to_entity)

            for source, destination in attribute_mapping:
                if source in entity_attributes:
                    select_mapping[destination] = source
        else:
            for source, destination in attribute_mapping:
                if source in self.select_mapping.keys():
                    select_mapping[destination] = self.select_mapping[source]
            # new_srcs = set(sources)
            # old_dests = set(self.current_select_mapping.keys())
            # common = new_srcs & old_dests
            # excluded = old_dests - sources
            # for val in self.current_select_mapping.values():
            #     if val in excluded:
            #         val = None

        self.select_mapping = select_mapping
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
