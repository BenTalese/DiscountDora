from sqlalchemy_utils import UUIDType

from domain.entities.shopping_list import ShoppingList
from domain.entities.stock_item import StockItem
from framework.persistence.infrastructure.persistence_context import db

ShoppingListStockItemAssociation = db.Table(
    ShoppingList.__name__ + StockItem.__name__,
    db.Column('shopping_list_id', UUIDType, db.ForeignKey(ShoppingList.__name__ + '.id')),
    db.Column('stock_item_id', UUIDType, db.ForeignKey(StockItem.__name__ + '.id'))
)
