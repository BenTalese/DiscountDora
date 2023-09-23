import asyncio
from typing import get_type_hints

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.query import Query
from flask_sqlalchemy.session import Session
from sqlalchemy.orm import joinedload, subqueryload
from varname import nameof

from application.services.ipersistence_context import IPersistenceContext
from application.services.iquerybuilder import IQueryBuilder
from domain.entities.stock_item import StockItem
from framework.persistence.infrastructure.seed import seed_initial_data_async
# TODO: Investigate getting IServiceProvider injected, do I need to register it against itself?

db = SQLAlchemy()

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

    def save_changes_async(self):
        db.session.commit()
        # asyncio.get_event_loop().run_in_executor(None, db.session.commit())

    # end IPersistenceContext Methods

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
        SqlAlchemyPersistenceContext.identity_map = {}
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
            x = SqlAlchemyPersistenceContext().get_entities(StockItem).include(nameof(StockItem.stock_level)).execute()
            v = 0
            await SqlAlchemyPersistenceContext().save_changes_async()

# TODO IMPORTANT!!! : I have a feeling once i change the model into the domain entity, it will stop tracking changes...
# ^ THIS MAY NOT BE AN ISSUE...test what happens on an update first before jumping to conclusions

# TODO: Find a home for this...
class SqlAlchemyQueryBuilder(IQueryBuilder):
    def __init__(self, session: sa_orm.scoped_session[Session], model_class, included_attributes = None):
        self._context = SqlAlchemyPersistenceContext._flask_app.app_context()
        with self._context:
            self.query: Query = session.query(model_class)
        self.included_attributes = included_attributes or []
        self.included_model = None
        self.model = model_class
        self.session = session

    def any(self, condition = None):
        with self._context:
            if condition:
                return self.query.filter(condition(self.model)).count() > 0
            else:
                return self.query.count() > 0

    def execute(self):
        with self._context:
            return [model_instance.to_entity() for model_instance in self.query.all()]

    def first(self, condition = None):
        with self._context:
            if condition:
                return self.where(condition).first()
            return self.query.one().to_entity()

    def first_by_id(self, *ids):
        result = self.session.get(*ids) # TODO: Wait how does this work? query is based on model, but this is based on what...?
        if result:
            return result.to_entity()
        else:
            raise Exception("Sequence contains no elements.") #TODO: Contains no elements, or not found...?

    def first_or_none(self, condition = None):
        with self._context:
            if condition:
                result = self.where(condition).first_or_none()
                return result.to_entity() if result else None
            result = self.query.one_or_none().to_entity()
            return result.to_entity() if result else None

    # # https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html
    def include(self, attribute_name: str):
        model_attribute = getattr(self.model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model)
        joined_query.query = self.query.options(joinedload(model_attribute))
        joined_query.included_attributes = [model_attribute]
        joined_query.included_model = model_attribute.comparator.entity.entity
        return joined_query

    def then_include(self, attribute_name: str):
        if not self.included_attributes:
            raise Exception("No relationship included.") #TODO: Better exception type
        model_attribute = getattr(self.included_model, attribute_name)
        joined_query = SqlAlchemyQueryBuilder(self.session, self.model, self.included_attributes)
        joined_query.query = self.query.options(subqueryload(*self.included_attributes, model_attribute))
        joined_query.included_attributes.append(model_attribute)
        joined_query.included_model = model_attribute.comparator.entity.entity
        return joined_query

    def where(self, condition):
        self.query = self.query.filter(condition(self.model))
        # TODO: I doubt this will work, probably need to do something like this:

        # def evaluate_expression(expression):
        #     try:
        #         result = eval(expression)
        #         return result
        #     except Exception as e:
        #         return f"Error: {e}"

        # def main():
        #     expression = "x == 5"
        #     result = evaluate_expression(expression)
        #     print(f"Result of expression '{expression}': {result}")

        # if __name__ == "__main__":
        #     main()

        return self
