from uuid import uuid4
from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.stock_level import StockLevel
from framework.persistence.infrastructure.persistence_context import db


class StockLevelModel(db.Model):
    __entity__ = StockLevel
    __tablename__ = StockLevel.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    description = Column(
        String(255))

    def to_entity(self) -> StockLevel:
        return StockLevel(
            id = EntityID(self.id),
            description = self.description)

    def get_key(self):
        return self.id
