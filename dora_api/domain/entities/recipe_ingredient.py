from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.stock_item import StockItem


@dataclass
class RecipeIngredient(BaseEntity):
    notes: str | None
    quantity: float | None
    stock_item: StockItem
    unit: str | None
    # C-4 Chunk 10 — nullable section grouping (DEC-3 option A). NULL means
    # the ingredient sits in the implicit "main" group; FK → RecipeSection
    # with ON DELETE SET NULL so deleting a section keeps its ingredients,
    # just unsectioned.
    section_id: UUID | None = None

    class Fields(BaseEntity.Fields):
        NOTES = "notes"
        QUANTITY = "quantity"
        STOCK_ITEM = "stock_item"
        UNIT = "unit"
        SECTION_ID = "section_id"
