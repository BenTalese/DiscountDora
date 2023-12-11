from uuid import uuid4
from sqlalchemy import Boolean, Column, Float, ForeignKey, LargeBinary, String
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.merchant import Merchant
from domain.entities.product import Product
from domain.entities.product_offer import ProductOffer
from framework.persistence.infrastructure.persistence_context import db
from framework.persistence.models.merchant_model import MerchantModel
from framework.persistence.models.product_offer_model import ProductOfferModel


class ProductModel(db.Model):
    __entity__ = Product
    __tablename__ = Product.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    brand = Column(String(255))

    # TODO: See console output on startup for issue
    current_offer = relationship(
        ProductOfferModel.__name__,
        lazy = "noload",
        uselist = False)

    historical_offers = relationship(
        ProductOfferModel.__name__,
        lazy = "noload")

    image = Column(LargeBinary)

    is_available = Column(Boolean)

    merchant = relationship(
        MerchantModel.__name__,
        lazy="noload")

    merchant_id = Column(
        UUIDType,
        ForeignKey(Merchant.__name__ + ".id"),
        nullable = False)

    merchant_stockcode = Column(
        String(255),
        nullable = False)

    name = Column(
        String(255),
        nullable = False)

    size_unit = Column(String(255))

    size_value = Column(Float)

    web_url = Column(String(255))

    def to_entity(self) -> Product:
        return Product(
            id = EntityID(self.id),
            brand = self.brand,
            current_offer = self.current_offer.to_entity() if self.current_offer else None,
            historical_offers = [offer.to_entity() for offer in self.historical_offers],
            image = self.image,
            is_available = self.is_available,
            merchant = self.merchant.to_entity() if self.merchant else None,
            merchant_stockcode = self.merchant_stockcode,
            name = self.name,
            size_unit = self.size_unit,
            size_value = self.size_value,
            web_url = self.web_url)

    def get_key(self):
        return self.id
