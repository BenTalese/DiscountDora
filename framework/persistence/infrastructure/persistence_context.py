import asyncio
import datetime
import uuid
from dataclasses import dataclass
from typing import List, get_type_hints

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.extension import sa_orm
from flask_sqlalchemy.query import Query
from flask_sqlalchemy.session import Session
from sqlalchemy import UUID, Column, ForeignKey, Integer, String
from sqlalchemy.orm import joinedload, relationship, subqueryload
from sqlalchemy_utils import UUIDType

from application.services.ipersistence_context import IPersistenceContext
from application.services.iquerybuilder import IQueryBuilder
from framework.persistence.infrastructure.seed import seed_initial_data_async

db = SQLAlchemy()

@dataclass
class Money:
    """A value object that represents money"""
    amount: int
    currency: str

@dataclass
class ChildThing:
    x: str

@dataclass
class Bid:
    """A value object that represents a bid placed on a listing by a buyer"""
    bidder_id: UUID
    price: Money
    childs: List[ChildThing]

@dataclass
class Listing:
    """An entity that represents a listing with an ask price and all the bids already placed on this item"""
    id: int
    name: str
    min_price: Money
    bids: List[Bid]

class ChildThingModel(db.Model):
    __tablename__ = "child"
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4) # <---------------------------- #TODO: APPLY EVERYWHERE!!
    x = Column(String)
    bid_id = Column(Integer,
                        ForeignKey("bid.idx"),
                        primary_key=True)

    def to_entity(self) -> ChildThing:
        return ChildThing(
            x = self.x
        )

class BidModel(db.Model):
    entity_type = Bid
    """ Stores Bid value object"""
    __tablename__ = "bid"
    # composite primary key
    listing_id = Column(UUIDType,
                        ForeignKey("listing.id"),
                        primary_key=True)

    # since bids are stored in an ordered collection (list), an index column is required
    idx = Column(Integer, primary_key=True)

    bidder_id = Column(UUIDType)
    price__amount = Column(Integer)
    price__currency = Column(String(3))

    # parent relationship
    listing = relationship("ListingModel", back_populates="bids", lazy="noload")

    childs = relationship("ChildThingModel", lazy="noload")

    def to_entity(self) -> Bid:
        return Bid(
            bidder_id=self.bidder_id,
            childs=[ChildThingModel.to_entity(child) for child in self.childs],
            price=Money(amount=self.price__amount, currency=self.price__currency)
        )

class ListingModel(db.Model):
    entity_type = Listing
    __tablename__ = "listing"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = Column(String(30))

    min_price__amount = Column(Integer)
    min_price__currency = Column(String(3))

    bids = relationship("BidModel",
                        order_by="BidModel.idx.asc()",
                        cascade="save-update, merge, delete, delete-orphan", lazy="noload")

    def to_entity(self) -> Listing:
        return Listing(
            id=self.id,
            name=self.name,
            min_price=Money(amount=self.min_price__amount, currency=self.min_price__currency),
            bids=[BidModel.to_entity(bid) for bid in self.bids] if self.bids else None
        )

class PersistenceContext(IPersistenceContext):
    flask_app: Flask
    model_classes: dict

    # TODO: Investigate getting IServiceProvider injected, do I need to register it against itself?

    # ---------------- IPersistenceContext Methods ----------------

    def add(self, entity):
        db.session.add(self.convert_to_model(entity))

    # TODO: Could do find method that uses identity map

    def get_entities(self, entity_type):
        with PersistenceContext.flask_app.app_context():
            model_class = self.get_model_class(entity_type)
            return SqlAlchemyQueryBuilder(db.session, model_class) # TODO: This won't work!
        #return db.session.query(model_class).all()#.options(noload('*')).all()

    def remove(self, entity):
        db.session.delete(self.convert_to_model(entity))

    async def save_changes_async(self):
        db.session.commit()
        # await asyncio.get_event_loop().run_in_executor(None, db.session.commit())

    # end IPersistenceContext Methods

    @classmethod # TODO: Class method?? cls for what? maybe make static instead
    async def initialise(cls, app: Flask):
        import framework.persistence.models  # Must make models visible to db.init_app()
        db.init_app(app)
        app.db = db # TODO: This seems like very bad practice
        PersistenceContext.flask_app = app
        PersistenceContext.model_classes = {
            mapper.class_.__name__: mapper.class_
            for mapper in db.Model.registry.mappers
        }
        with app.app_context():
            if app.config.get('DEBUG'): # TODO Options interface, abstract away how settings are stored
                db.drop_all()
                db.create_all()
                Migrate().init_app(app, db) # TODO: Do i need a migrate here?...
                listing = ListingModel()
                listing.name = "Listing"
                listing.min_price__amount = 1
                listing.min_price__currency = "AUD"

                child1 = ChildThingModel()
                child1.x = "AHHH"

                child2 = ChildThingModel()
                child2.x = "OHHH"

                bid = BidModel()
                bid.idx = 1
                bid.price__amount = 1
                bid.price__currency = "AUD"
                bid.childs = [child1, child2]
                listing.bids = [bid]

                db.session.add(listing)
                db.session.commit()

                result = db.session.query(ListingModel).all()

                await seed_initial_data_async(PersistenceContext())
            else:
                db.create_all() #TODO: This doesn't handle migrations on existing tables
                Migrate().init_app(app, db) # TODO: Create, mirate, or both?

    def get_model_class(self, entity_type):
        for model_class in self.model_classes.items():
            if model_class[0].replace("Model", "") == entity_type.__name__:
                return model_class[1]
        raise Exception(f"Model not found for: {entity_type.__name__}") #TODO: Test this is a good message

    def convert_to_model(self, entity):
        model_class = self.get_model_class(type(entity))
        model_data = vars(entity).copy()
        for attr_name, type_hint in get_type_hints(entity).items():
            if (type_hint == uuid
                or type_hint == datetime):
                continue

            if "entities" in type_hint.__module__ and model_data[attr_name]:
                model_data[attr_name + '_id'] = model_data[attr_name].id
                del model_data[attr_name]

        x = model_class(**model_data)
        return model_class(**model_data)

    @staticmethod
    def test(app):
        with app.app_context():
            # result = app.db.session.query(ListingModel).all()
            # g = result[0].bids[0].listing
            x = PersistenceContext().get_entities(Listing).execute()
            v = 0

# TODO IMPORTANT!!! : I have a feeling once i change the model into the domain entity, it will stop tracking changes...
# ^ THIS MAY NOT BE AN ISSUE...test what happens on an update first before jumping to conclusions

# TODO: Find a home for this...
# TODO: Match up IQueryBuilder to this
class SqlAlchemyQueryBuilder(IQueryBuilder):
    # def __init__(self, app_context: AppContext, session: sa_orm.scoped_session[Session], entity_type, model_class):
    def __init__(self, session: sa_orm.scoped_session[Session], model_class):
        self.session = session
        self.model = model_class
        self.query: Query = session.query(model_class)
        self.included = None

    def any(self, condition = None):
        if condition:
            return self.query.filter(condition(self.model)).count() > 0
        else:
            return self.query.count() > 0

    def execute(self):
        with PersistenceContext.flask_app.app_context():
            return [model_instance.to_entity() for model_instance in self.query.all()]

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

    # https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html
    def include(self, attribute_name: str):
        # a2 = x.add_columns()
        # a3 = x.add_entity()
        # a4 = x.count() #TODO: Want this on save
        # a6 = x.from_statement()
        # a7 = x.options()
        # a8 = x.params()
        # a9 = x.select_from()
        model_attribute = getattr(self.model, attribute_name)
        self.query.options(joinedload(model_attribute))
        self.included = model_attribute.comparator.entity.entity
        return self

    def then_include(self, attribute_name: str):
        if not self.included:
            raise Exception("No relationship included.") #TODO: Better exception type
        model_attribute = getattr(self.included, attribute_name)
        self.query.options(subqueryload(model_attribute))
        self.included = model_attribute.comparator.entity.entity
        return self

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
