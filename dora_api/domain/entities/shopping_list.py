from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Provenance of a shopping-list line — why it ended up on the list.
# Used by the UI to render "auto: low stock" / "auto: recipe X" chips
# and by analytics to tell user-initiated adds from auto-generated ones.
# Plain str sentinels (not Enum) so SQLAlchemy stores them as varchar
# without bind-parameter dancing.
ADDED_VIA_MANUAL = "manual"
ADDED_VIA_AUTO_LOW_STOCK = "auto_low_stock"
ADDED_VIA_AUTO_ESSENTIAL = "auto_essential"
ADDED_VIA_AUTO_FLAGGED = "auto_flagged"
ADDED_VIA_AUTO_RECIPE = "auto_recipe"
ADDED_VIA_AUTO_MEAL_PLAN = "auto_meal_plan"
ADDED_VIA_AUTO_FREQUENTLY_ADDED = "auto_frequently_added"

ADDED_VIA_VALUES = {
    ADDED_VIA_MANUAL,
    ADDED_VIA_AUTO_LOW_STOCK,
    ADDED_VIA_AUTO_ESSENTIAL,
    ADDED_VIA_AUTO_FLAGGED,
    ADDED_VIA_AUTO_RECIPE,
    ADDED_VIA_AUTO_MEAL_PLAN,
    ADDED_VIA_AUTO_FREQUENTLY_ADDED,
}


@dataclass
class ShoppingListLine(BaseEntity):
    shopping_list_id: UUID
    stock_item_id: UUID
    quantity: int | None = None
    is_ticked: bool = False
    selected_product_id: UUID | None = None
    sequence: int = 0
    # X5 provenance. "manual" for user-typed adds; one of the auto_* values
    # when the line came from /auto-generate or the auto_add_when_low
    # trigger. If a user later edits the line (quantity/product), the
    # caller flips this back to "manual" so the chip disappears.
    added_via: str = ADDED_VIA_MANUAL
    added_at: datetime | None = None
    # N6 snapshot pair, captured the first time a line is ticked. They freeze
    # the merchant offer at "moment of pick" so historic reporting (savings,
    # spend-by-merchant) stays honest after prices move. Both stay None for
    # lines that were never ticked (e.g. archived without finishing).
    picked_offer_price: float | None = None
    list_price_at_pick: float | None = None

    class Fields(BaseEntity.Fields):
        SHOPPING_LIST_ID = "shopping_list_id"
        STOCK_ITEM_ID = "stock_item_id"
        QUANTITY = "quantity"
        IS_TICKED = "is_ticked"
        SELECTED_PRODUCT_ID = "selected_product_id"
        SEQUENCE = "sequence"
        ADDED_VIA = "added_via"
        ADDED_AT = "added_at"
        PICKED_OFFER_PRICE = "picked_offer_price"
        LIST_PRICE_AT_PICK = "list_price_at_pick"


@dataclass
class ShoppingList(BaseEntity):
    name: str
    created_at: datetime
    is_primary: bool = False
    is_archived: bool = False
    # `is_in_progress` is the "I'm actively shopping right now" state. While
    # true, the UI locks editing (add/remove lines, rename) and emphasises
    # ticking off. Transitions:
    #   planning    -> in_progress: user clicks Start shopping
    #   in_progress -> planning   : user clicks Stop shopping (no archive)
    #   in_progress -> archived   : user clicks Finish (the finish endpoint
    #                               archives and `is_in_progress` becomes
    #                               irrelevant once archived).
    is_in_progress: bool = False
    completed_at: datetime | None = None
    # Lines hang off the list. Loaded explicitly by handlers that need them
    # (matches the noload pattern used elsewhere — table_mappings sets
    # lazy="noload"). Default empty so seed/in-memory construction works.
    lines: List[ShoppingListLine] = field(default_factory=list)

    class Fields(BaseEntity.Fields):
        NAME = "name"
        IS_PRIMARY = "is_primary"
        IS_ARCHIVED = "is_archived"
        IS_IN_PROGRESS = "is_in_progress"
        CREATED_AT = "created_at"
        COMPLETED_AT = "completed_at"
        LINES = "lines"
