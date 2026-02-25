from dataclasses import dataclass
from typing import List
from dora_api.domain.entities.base_entity import BaseEntity

from dora_api.domain.entities.stock_item import StockItem


@dataclass(slots=True)
class ShoppingList(BaseEntity):
    items: List[StockItem]
