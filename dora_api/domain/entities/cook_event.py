from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class CookEvent(BaseEntity):
    """Append-only log of "the user actually cooked this recipe today".

    Written by the /recipes/<id>/cook endpoint alongside the existing
    `available_meals` bump on Recipe. The row is per-cook (one POST →
    one CookEvent), so a household that batch-cooks Sunday and then
    reheats through the week still leaves a single event on Sunday.

    Consumed by the Stock Item detail's History tab: any CookEvent for
    a recipe whose ingredient list references this stock item shows up
    as "Used in <recipe>". The join is done at projection time in
    `get_stock_item_detail.py` — no denormalisation onto CookEvent
    itself, which would balloon on multi-ingredient recipes.

    `recipe_name` is denormalised so a rename or delete of the recipe
    doesn't blank a historical event's label — same policy as
    `StockItemWasteEvent.stock_item_name`.
    """
    recipe_id: UUID | None
    recipe_name: str
    meals_cooked: int
    cooked_by_user_id: UUID | None
    occurred_at: datetime

    class Fields(BaseEntity.Fields):
        RECIPE_ID = "recipe_id"
        RECIPE_NAME = "recipe_name"
        MEALS_COOKED = "meals_cooked"
        COOKED_BY_USER_ID = "cooked_by_user_id"
        OCCURRED_AT = "occurred_at"
