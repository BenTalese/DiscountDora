from dataclasses import dataclass
from typing import List
import uuid

from domain.entities.stock_item import StockItem


@dataclass
class ShoppingList:
    id: uuid
    items: List[StockItem]
