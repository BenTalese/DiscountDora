from typing import List
import uuid

from domain.entities.stock_item import StockItem


class ShoppingList:
    id: uuid
    items: List[StockItem]
