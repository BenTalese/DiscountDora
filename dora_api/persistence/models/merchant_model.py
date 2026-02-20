from uuid import uuid4
import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column
from sqlalchemy_utils import UUIDType

from domain.entities.merchant import Merchant
from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID


class MerchantModel(db.Model):
    __entity__ = Merchant
    __tablename__ = Merchant.__name__

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(String(255))

    def to_entity(self) -> Merchant:
        entity = Merchant(name = self.name)
        entity.id = EntityID(self.id)
        return entity

    @classmethod
    def from_entity(cls, merchant: Merchant):
        model = cls()
        model.id = merchant.id.value
        model.name = merchant.name
        return model
