from dataclasses import dataclass, field
from datetime import date, datetime
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


# P6-01 lifecycle status — the single source of truth for where a list is
# in the shop loop, replacing the old is_archived / is_in_progress flags.
#   draft    : being assembled / edited (the old "planning", non-archived,
#              not-in-progress state).
#   shopping : actively being shopped right now (was is_in_progress).
#   done     : finished or archived (was is_archived). completed_at carries
#              the timestamp.
# Plain str sentinels (not Enum) so SQLAlchemy stores them as varchar,
# matching the ADDED_VIA_* convention above.
SHOPPING_LIST_STATUS_DRAFT = "draft"
SHOPPING_LIST_STATUS_SHOPPING = "shopping"
SHOPPING_LIST_STATUS_DONE = "done"

SHOPPING_LIST_STATUS_VALUES = {
    SHOPPING_LIST_STATUS_DRAFT,
    SHOPPING_LIST_STATUS_SHOPPING,
    SHOPPING_LIST_STATUS_DONE,
}


@dataclass
class ShoppingListLine(BaseEntity):
    shopping_list_id: UUID
    # C-7 Chunk 3 — a line is anchored by stock_item_id OR product_id
    # (or both, when a product is nested under a stock item). At least
    # one MUST be set; enforced by a DB CHECK + the add-line validator.
    stock_item_id: UUID | None = None
    product_id: UUID | None = None
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
    # P2-02 purchase memory: what the shopper *actually* paid (per unit) and
    # who they actually bought it from, when those differ from the planned
    # offer. Either may be set independently — a user might confirm the
    # merchant on the chip but type a different till-receipt price, or vice
    # versa. Both NULL = use the picked_offer_price snapshot as the historic
    # paid price (the previous behaviour). When set, actual_unit_price wins
    # for totals and for the assistant's price-history queries.
    actual_unit_price: float | None = None
    purchased_merchant_id: UUID | None = None

    class Fields(BaseEntity.Fields):
        SHOPPING_LIST_ID = "shopping_list_id"
        STOCK_ITEM_ID = "stock_item_id"
        PRODUCT_ID = "product_id"
        QUANTITY = "quantity"
        IS_TICKED = "is_ticked"
        SELECTED_PRODUCT_ID = "selected_product_id"
        SEQUENCE = "sequence"
        ADDED_VIA = "added_via"
        ADDED_AT = "added_at"
        PICKED_OFFER_PRICE = "picked_offer_price"
        LIST_PRICE_AT_PICK = "list_price_at_pick"
        ACTUAL_UNIT_PRICE = "actual_unit_price"
        PURCHASED_MERCHANT_ID = "purchased_merchant_id"


@dataclass
class ShoppingList(BaseEntity):
    name: str
    created_at: datetime
    # Lifecycle status (see SHOPPING_LIST_STATUS_* above). Transitions:
    #   draft    -> shopping : user clicks Start shopping
    #   shopping -> draft    : user clicks Stop shopping (no finish)
    #   draft/shopping -> done : Finish (restock + snapshot) or plain archive
    #   done     -> draft    : Reopen (reverses the finish from finish_snapshot)
    status: str = SHOPPING_LIST_STATUS_DRAFT
    completed_at: datetime | None = None
    # P6-01 Chunk 7. Optional shopping day the user is planning this list
    # for. Drives the landing-page pick (today's list wins), the selector's
    # sort, and the shopping-day banner. Never required — a list without a
    # planned date still behaves the same as today.
    planned_shop_date: date | None = None
    # P6-01 server-owned undo. Set when a list is finished: a JSON snapshot of
    # each ticked item's stock level before restock, so Reopen reverses it
    # without trusting a client-supplied snapshot. None when the list has never
    # been finished or has since been reopened. (Chunk 2 dropped the
    # primary-related fields from the snapshot — primary is now inferred.)
    finish_snapshot: str | None = None
    # Lines hang off the list. Loaded explicitly by handlers that need them
    # (matches the noload pattern used elsewhere — table_mappings sets
    # lazy="noload"). Default empty so seed/in-memory construction works.
    lines: List[ShoppingListLine] = field(default_factory=list)

    @property
    def is_done(self) -> bool:
        return self.status == SHOPPING_LIST_STATUS_DONE

    @property
    def is_shopping(self) -> bool:
        return self.status == SHOPPING_LIST_STATUS_SHOPPING

    @property
    def is_draft(self) -> bool:
        return self.status == SHOPPING_LIST_STATUS_DRAFT

    class Fields(BaseEntity.Fields):
        NAME = "name"
        STATUS = "status"
        CREATED_AT = "created_at"
        COMPLETED_AT = "completed_at"
        FINISH_SNAPSHOT = "finish_snapshot"
        PLANNED_SHOP_DATE = "planned_shop_date"
        LINES = "lines"
