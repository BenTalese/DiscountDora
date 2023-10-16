import uuid
from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from domain.entities.base_entity import EntityID

from domain.entities.shopping_list import ShoppingList
from framework.persistence.infrastructure.persistence_context import db
from framework.persistence.models.stock_item_model import StockItemModel


class ShoppingListModel(db.Model):
    __entity__ = ShoppingList
    __tablename__ = ShoppingList.__name__

    id = Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)

    items = relationship(StockItemModel.__name__, lazy="noload")

    def to_entity(self) -> ShoppingList:
        return ShoppingList(
            id = EntityID(self.id),
            items = [item.to_entity() for item in self.items])
