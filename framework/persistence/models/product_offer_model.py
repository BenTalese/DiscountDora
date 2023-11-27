from uuid import uuid4
from sqlalchemy import Column, DateTime, Float, ForeignKey
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.product import Product
from domain.entities.product_offer import ProductOffer
from framework.persistence.infrastructure.persistence_context import db


class ProductOfferModel(db.Model):
    __entity__ = ProductOffer
    __tablename__ = ProductOffer.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    offered_on = Column(DateTime(timezone = True))

    price_now = Column(Float)

    price_was = Column(Float)

    product_id = Column(
        UUIDType,
        ForeignKey(Product.__name__ + ".id"),
        nullable = False)

    def to_entity(self) -> ProductOffer:
        return ProductOffer(
            id = EntityID(self.id),
            offered_on = self.offered_on,
            price_now = self.price_now,
            price_was = self.price_was)

    def get_key(self):
        return self.id
