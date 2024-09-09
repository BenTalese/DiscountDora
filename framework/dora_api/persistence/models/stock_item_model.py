from uuid import uuid4

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        LargeBinary, String)
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.stock_group import StockGroup
from domain.entities.stock_item import StockItem
from domain.entities.stock_level import StockLevel
from domain.entities.stock_location import StockLocation
from framework.dora_api.persistence.models.stock_group_model import \
    StockGroupModel
from framework.dora_api.persistence.models.stock_level_model import \
    StockLevelModel
from framework.dora_api.persistence.models.stock_location_model import \
    StockLocationModel
from framework.dora_api.persistence.persistence_context import db


# TODO: for all models figure out "required", "min value", "relationship existence constraint" etc...
class StockItemModel(db.Model):
    __entity__ = StockItem
    __tablename__ = StockItem.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    days_until_stocktake_alert = Column(Integer)

    image = Column(LargeBinary)

    name = Column(String(255))

    notes = Column(String(255))

    shopping_lists = relationship(
        'ShoppingListModel',
        secondary = 'ShoppingListStockItem',
        back_populates = 'items',
        lazy = "noload")

    stock_group = relationship(
        StockGroupModel.__name__,
        lazy="noload")

    stock_group_id = Column(
        UUIDType,
        ForeignKey(StockGroup.__name__ + ".id"),
        nullable = True)

    stock_level = relationship(
        StockLevelModel.__name__,
        lazy="noload")

    stock_level_id = Column(
        UUIDType,
        ForeignKey(StockLevel.__name__ + ".id"))

    stock_level_last_updated = Column(DateTime(timezone = True))

    stock_location = relationship(
        StockLocationModel.__name__,
        lazy="noload")

    stock_location_id = Column(
        UUIDType,
        ForeignKey(StockLocation.__name__ + ".id"),
        nullable = True)

    stocktake_alerts_are_enabled = Column(Boolean)

    def to_entity(self) -> StockItem:
        return StockItem(
            id = EntityID(self.id),
            stock_location = self.stock_location.to_entity() if self.stock_location else None,
            name = self.name,
            stock_level = self.stock_level.to_entity() if self.stock_level else None,
            stock_level_last_updated = self.stock_level_last_updated)

    def get_key(self):
        return self.id
