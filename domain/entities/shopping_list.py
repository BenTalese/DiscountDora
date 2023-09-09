from typing import List
import uuid

from domain.entities.stock_item import StockItem


class ShoppingList:
    def __init__(
            self,
            id: uuid,
            items: List[StockItem]):
        self.id = id
        self.items = items