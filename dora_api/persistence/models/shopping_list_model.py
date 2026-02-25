from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import UUIDType

from dora_api.app import db
from dora_api.domain.entities.base_entity import EntityID
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.persistence.models.stock_item_model import StockItemModel


class ShoppingListModel(db.Model):
    __entity__ = ShoppingList
    __tablename__ = ShoppingList.__name__

    id: Mapped[UUID] = mapped_column(
        UUIDType,
        primary_key=True,
        default=uuid4
    )

    items = relationship(
        'StockItemModel',
        secondary = 'ShoppingListStockItem',
        back_populates = 'shopping_lists',
        lazy = "noload"
    )

    def to_entity(self) -> ShoppingList:
        _Entity = ShoppingList(
            items = [si.to_entity() for si in self.items]
        )
        _Entity.id = EntityID(self.id)
        return _Entity

    @classmethod
    def from_entity(cls, shopping_list: ShoppingList) -> 'ShoppingListModel':
        _Model = cls()
        _Model.id = shopping_list.id.value
        _Model.items = [StockItemModel.from_entity(si) for si in shopping_list.items]
        return _Model
