from dataclasses import dataclass

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.stock_item import StockItem


@dataclass
class RecipeIngredient(BaseEntity):
    notes: str | None
    quantity: float | None
    stock_item: StockItem
    unit: str | None

    class Fields(BaseEntity.Fields):
        NOTES = "notes"
        QUANTITY = "quantity"
        STOCK_ITEM = "stock_item"
        UNIT = "unit"
