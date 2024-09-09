from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.stock_location import StockLocation
from framework.dora_api.persistence.persistence_context import db


class StockLocationModel(db.Model):
    __entity__ = StockLocation
    __tablename__ = StockLocation.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    name = Column(
        String(255))

    def to_entity(self) -> StockLocation:
        return StockLocation(
            id = EntityID(self.id),
            name = self.name)

    def get_key(self):
        return self.id
