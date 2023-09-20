import asyncio

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.session import Session
from sqlalchemy.orm import Query

from application.services.ipersistence_context import IPersistenceContext
from application.services.iquerybuilder import IQueryBuilder

db = SQLAlchemy()

class PersistenceContext(IPersistenceContext):
    flask_app: Flask

    model_classes: dict

    # TODO: Investigate getting IServiceProvider injected, do I need to register it against itself?

    # ---------------- IPersistenceContext Methods ----------------

    def add(self, entity):
        db.session.add(self.convert_to_model(entity))

    def get_entities(self, entity_type):
        with PersistenceContext.flask_app.app_context():
            model_class = self.get_model_class(entity_type)
            return SqlAlchemyQueryBuilder(db.session, entity_type, model_class) # TODO: This won't work!
        #return db.session.query(model_class).all()#.options(noload('*')).all()

    def remove(self, entity):
        db.session.delete(self.convert_to_model(entity))

    async def save_changes_async(self):
        await asyncio.get_event_loop().run_in_executor(None, db.session.commit())

    # end IPersistenceContext Methods

    @classmethod
    def initialise(cls, app: Flask):
        PersistenceContext.flask_app = app
        db.app = app
        import framework.persistence.models
        db.init_app(app)
        PersistenceContext.model_classes = {
            mapper.class_.__name__: mapper.class_
            for mapper in db.Model.registry.mappers
        }
        with app.app_context():
            if app.config.get('DEBUG'): #TODO Options interface, abstract away how settings are stored
                # db.drop_all()
                db.create_all() #TODO: This doesn't handle migrations on existing tables
                #db.seed()  #TODO
                #db.session.add(testconfig)

                # test = StockItem()
                # test.id = uuid.uuid4()
                # test.name = "TEST NAME"
                # test.stock_level_last_updated_on_utc = datetime.now()
                # db.session.add(StockItemModel(**test.__dict__))
                # db.session.commit()

                #x = PersistenceContext().find_model_for_entity(Test)
                #v = 0
            else:
                db.create_all() #TODO: This doesn't handle migrations on existing tables

    def seed_initial_data() -> None:
        pass

    def get_model_class(self, entity_type):
        for model_class in self.model_classes.items():
            if model_class[0].rstrip("Model") == entity_type.__name__:
                return model_class[1]
        raise Exception(f"Model not found for: {entity_type.__name__}") #TODO: Test this is a good message

    def convert_to_model(self, entity):
        model_class = self.get_model_class(type(entity))
        return model_class(**vars(entity))

# TODO IMPORTANT!!! : I have a feeling once i change the model into the domain entity, it will stop tracking changes...

# TODO: Find a home for this...
class SqlAlchemyQueryBuilder(IQueryBuilder):
    # def __init__(self, app_context: AppContext, session: sa_orm.scoped_session[Session], entity_type, model_class):
    def __init__(self, session: sa_orm.scoped_session[Session], entity_type, model_class):
        self.session = session
        self.entity_type = entity_type
        self.model = model_class
        self.query: Query = session.query(model_class)

    def any(self, condition = None):
        if condition:
            return self.query.filter(condition(self.model)).count() > 0
        else:
            return self.query.count() > 0

    def execute(self):
        with PersistenceContext.flask_app.app_context():
            query_result = self.query.all()
            entities = []
            for model_instance in query_result:
                entity = self.entity_type()
                for key, value in model_instance.__dict__.items():
                    setattr(entity, key, value)
                entities.append(entity)
            return entities

    # def find():
    #     pass # .get() # Investigate, .get() is on session and is apparently the one to use from docs, see if it executes

    def first(self, condition = None):
        if condition:
            return self.where(condition).first()
        return self.query.one()

    def first_by_id(self, id):
        result = self.session.get(id) # TODO: Wait how does this work? query is based on model, but this is based on what...?
        if result:
            return result
        else:
            raise Exception("Sequence contains no elements.") #TODO: Contains no elements, or not found...?

    def first_or_none(self, condition = None):
        if condition:
            return self.where(condition).first_or_none()
        return self.query.one_or_none()

    # FIXME: This is crap, no no no, will execute
    # https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html
    # def select(self, selector):
    #     return [selector(entity) for entity in self.query.all()]

    def where(self, condition):
        self.query = self.query.filter(condition(self.model))
        return self
