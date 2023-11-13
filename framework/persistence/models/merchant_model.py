import uuid

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.merchant import Merchant
from framework.persistence.infrastructure.persistence_context import db


class MerchantModel(db.Model):
    __entity__ = Merchant
    __tablename__ = Merchant.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)

    name = Column(String(255))

    def to_entity(self) -> Merchant:
        return Merchant(
            id = EntityID(self.id),
            name = self.name)

    def get_key(self):
        return self.id
