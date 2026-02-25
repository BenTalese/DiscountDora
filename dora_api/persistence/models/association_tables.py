from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_item import StockItem
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy_utils import UUIDType

from dora_api.app import db

ShoppingListStockItemAssociation = Table(
    ShoppingList.__name__ + StockItem.__name__,
    db.metadata,
    Column(
        "shopping_list_id",
        UUIDType,
        ForeignKey(ShoppingList.__name__ + '.id'),
        primary_key=True
    ),
    Column(
        "stock_item_id",
        UUIDType,
        ForeignKey(StockItem.__name__ + '.id'),
        primary_key=True
    )
)
