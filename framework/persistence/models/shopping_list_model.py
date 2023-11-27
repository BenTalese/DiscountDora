from uuid import uuid4
from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from domain.entities.base_entity import EntityID
from domain.entities.shopping_list import ShoppingList
from framework.persistence.infrastructure.persistence_context import db


class ShoppingListModel(db.Model):
    __entity__ = ShoppingList
    __tablename__ = ShoppingList.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid4)

    items = relationship(
        'StockItemModel',
        secondary = 'ShoppingListStockItem',
        back_populates = 'shopping_lists',
        lazy = "noload")

    def to_entity(self) -> ShoppingList:
        return ShoppingList(
            id = EntityID(self.id),
            items = [item.to_entity() for item in self.items])

    def get_key(self):
        return self.id
