import uuid

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from domain.entities.stock_location import StockLocation
from framework.persistence.infrastructure.persistence_context import db


class StockLocationModel(db.Model):
    __entity__ = StockLocation
    __tablename__ = StockLocation.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)

    description = Column(
        String(255))

    def to_entity(self) -> StockLocation:
        return StockLocation(
            id = self.id,
            description = self.description)
