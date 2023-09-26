import uuid

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from domain.entities.stock_level import StockLevel
from framework.persistence.infrastructure.persistence_context import db


class StockLevelModel(db.Model):
    __tablename__ = StockLevel.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)

    description = Column(
        String(255))

    def to_entity(self) -> StockLevel:
        return StockLevel(
            id = self.id,
            description = self.description)
