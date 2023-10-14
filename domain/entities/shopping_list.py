from dataclasses import dataclass
from typing import List
from domain.entities.base_entity import BaseEntity

from domain.entities.stock_item import StockItem


@dataclass
class ShoppingList(BaseEntity):
    items: List[StockItem] = None
