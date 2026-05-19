from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.stock_item import StockItem


@dataclass
class RecipeIngredient(BaseEntity):
    NOTES = "notes"
    notes: str | None

    QUANTITY = "quantity"
    quantity: float | None

    STOCK_ITEM = "stock_item"
    stock_item: StockItem

    UNIT = "unit"
    unit: str | None
