from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.stock_group import StockGroup
from framework.dora_api.app import db


class StockGroupModel(db.Model):
    __entity__ = StockGroup
    __tablename__ = StockGroup.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    name = Column(String(255))

    def to_entity(self) -> StockGroup:
        return StockGroup(
            id = EntityID(self.id),
            name = self.name)

    def get_key(self):
        return self.id
