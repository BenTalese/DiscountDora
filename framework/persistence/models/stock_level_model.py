from uuid import uuid4
from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.stock_level import StockLevel
from framework.persistence.infrastructure.persistence_context import db


""" TODO: Look into how to make a verification check to ensure newly added properties are added in these locations:
    - Domain
    - Dto
    - Dto mapping
    - View model
    - View model mapping
    - UI model
    - DB model
    - Entity mapping
"""
class StockLevelModel(db.Model):
    __entity__ = StockLevel
    __tablename__ = StockLevel.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    description = Column(String(255))

    sequence = Column(Integer)

    def to_entity(self) -> StockLevel:
        return StockLevel(
            id = EntityID(self.id),
            description = self.description,
            sequence = self.sequence)

    def get_key(self):
        return self.id
