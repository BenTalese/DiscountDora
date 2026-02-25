from uuid import UUID, uuid4

from sqlalchemy import Boolean, Float, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.product import Product
from dora_api.persistence.models.merchant_model import MerchantModel
from dora_api.persistence.models.product_historic_offer_model import \
    ProductHistoricOfferModel
from dora_api.persistence.models.product_offer_model import ProductOfferModel


class ProductModel(db.Model):
    __entity__ = Product
    __tablename__ = Product.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    brand: Mapped[str | None] = mapped_column(String(255))

    current_offer: Mapped[ProductOfferModel] = relationship(
        lazy = "noload",
        uselist = False
    )

    historic_offers: Mapped[list[ProductHistoricOfferModel]] = relationship(
        lazy="noload"
    )

    image: Mapped[bytes | None] = mapped_column(LargeBinary)

    is_active: Mapped[bool] = mapped_column(Boolean)

    is_available: Mapped[bool] = mapped_column(Boolean)

    merchant: Mapped[MerchantModel] = relationship(
        lazy="noload"
    )

    merchant_id: Mapped[UUID] = mapped_column(
        UUIDType,
        ForeignKey(Merchant.__name__ + ".id"),
        nullable=False
    )

    merchant_stockcode: Mapped[str | None] = mapped_column(
        String(255),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    size: Mapped[str] = mapped_column(String(255))

    size_unit: Mapped[str] = mapped_column(String(255))

    size_value: Mapped[float] = mapped_column(Float)

    web_url: Mapped[str | None] = mapped_column(String(255))

    def to_entity(self) -> Product:
        _Entity = Product(
            brand = self.brand,
            current_offer = self.current_offer.to_entity() if self.current_offer else None,  # type: ignore
            historic_offers = [offer.to_entity() for offer in self.historic_offers],
            image = self.image,
            is_active = self.is_active,
            is_available = self.is_available,
            merchant = self.merchant.to_entity() if self.merchant else None,  # type: ignore
            merchant_stockcode = self.merchant_stockcode,
            name = self.name,
            size = self.size,
            size_unit = self.size_unit,
            size_value = self.size_value,
            web_url = self.web_url)

        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, product: Product) -> 'ProductModel':
        _Model = cls()
        _Model.id = product.id.value
        _Model.brand = product.brand
        _Model.current_offer = ProductOfferModel.from_entity(product.current_offer) if product.current_offer else None  # type: ignore
        _Model.historic_offers = [ProductHistoricOfferModel.from_entity(ho) for ho in product.historic_offers]
        _Model.image = product.image
        _Model.is_active = product.is_active
        _Model.is_available = product.is_available
        _Model.merchant = MerchantModel.from_entity(product.merchant) if product.merchant else None   # type: ignore
        #_Model.merchant_id = ???  # TODO: ???
        _Model.merchant_stockcode = product.merchant_stockcode
        _Model.name = product.name
        _Model.size = product.size
        _Model.size_unit = product.size_unit
        _Model.size_value = product.size_value
        _Model.web_url = product.web_url
        return _Model
