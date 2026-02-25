from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer


class ProductOfferModel(db.Model):
    __entity__ = ProductOffer
    __tablename__ = ProductOffer.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    offered_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    price_now: Mapped[float] = mapped_column(Float)

    price_was: Mapped[float] = mapped_column(Float)

    product_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey(Product.__name__ + ".id"),
        nullable=False
    )

    def to_entity(self) -> ProductOffer:
        _Entity = ProductOffer(
            offered_on = self.offered_on,
            price_now = self.price_now,
            price_was = self.price_was
        )

        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, product_offer: ProductOffer) -> 'ProductOfferModel':
        _Model = cls()
        _Model.id = product_offer.id.value
        _Model.offered_on = product_offer.offered_on
        _Model.price_now = product_offer.price_now
        _Model.price_was = product_offer.price_was
        # FIXME: Do i need to do this? If so...how? What was my old convert code doing?
        #_Model.product_id = product_historic_offer. ???
        return _Model
