from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.merchant import Merchant


class MerchantModel(db.Model):
    __entity__ = Merchant
    __tablename__ = Merchant.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(String(255))

    def to_entity(self) -> Merchant:
        _Entity = Merchant(name = self.name)
        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, merchant: Merchant) -> 'MerchantModel':
        _Model = cls()
        _Model.id = merchant.id.value
        _Model.name = merchant.name
        return _Model
