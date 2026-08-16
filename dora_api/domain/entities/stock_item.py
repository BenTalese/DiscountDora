from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation


@dataclass
class StockItem(BaseEntity):
    # PROPOSAL_STOCKTAKE_MODE — per-item cadence dial (`days_until_
    # stocktake_alert`) retired in the 2026-07-04 cleanup. The queue now
    # resolves cadence server-side (global default + Auto + Essential +
    # Low/Out bump); see `features/stocktake/cadence.py`.
    name: str
    notes: str | None
    stock_group: StockGroup | None
    stock_level_last_updated: datetime
    stock_level: StockLevel
    stock_location: StockLocation | None
    stocktake_alerts_are_enabled: bool
    expiry_date: date | None = None
    is_essential: bool = False
    # the user-curated Store this item is usually bought from. Plain
    # UUID (no relationship object), nullable. Drives shopping-list grouping
    # (PROPOSAL_PRODUCTS_AS_OVERLAY §3.3) and a "favourite store" hint on the
    # stock-item detail; users can override at trip-build time. SET NULL on
    # store delete so removing a store doesn't break the items that referenced
    # it — they fall back to "no usual store".
    usual_store_id: UUID | None = None
    # Nutrition complex-mode — the food in the nutrition catalogue whose
    # per-100g values describe this item. Set only by explicit human
    # confirmation through the lookup (P12 No-invent: a fuzzy name match is a
    # *suggestion*, never a saved link). Plain UUID, no relationship object,
    # SET NULL on food delete so re-importing or dropping a dataset can't take
    # stock items with it — the link just goes quiet and the item shows as
    # unlinked again.
    nutrition_food_id: UUID | None = None
    # "Don't track nutrition for this item" — the explicit opt-out behind the
    # auto-suggestion. Toilet paper has no calories and never will, so an item
    # the user has waved off drops out of the unmatched queue permanently
    # instead of being re-suggested on every visit. Distinct from
    # `nutrition_food_id is None`, which means "unlinked, still worth asking".
    nutrition_ignored: bool = False
    # FU-511 — per-item `auto_add_when_low` was collapsed into
    # `AppSetting.auto_add_mode` (off / essential_only / all). Auto-add
    # now derives from that install-wide setting + this item's
    # `is_essential`, not a per-item toggle.
    # "I've cracked open the jar" — true while the item is being actively
    # consumed. `opened_on` is set automatically when `is_open` flips to
    # True; flipping back to False clears it.
    is_open: bool = False
    opened_on: date | None = None
    # X1: distinct from stock_level_last_updated. A "check" is the user
    # confirming the current level is correct without changing it.
    # Updating the level updates BOTH timestamps; clicking "Still
    # correct" in stocktake mode only moves this one. None = never
    # checked — under the redesigned stocktake engine (PROPOSAL_
    # STOCKTAKE_MODE §4.1) the queue baselines against
    # COALESCE(last_checked_at, stock_level_last_updated), so a never-
    # checked item gets a natural grace period from its creation moment.
    last_checked_at: datetime | None = None
    # PROPOSAL_STOCKTAKE_MODE §5 — the "Push 3 days" resolution verb.
    # Queue excludes items where snoozed_until > now. Cleared when the
    # item is later Checked / Set level / Muted (via those endpoints,
    # not here). Nullable = "not snoozed".
    snoozed_until: datetime | None = None
    # Merchant products linked to this stock item, used by the product-search
    # flow to surface deals and by the detail view to show "what merchant
    # SKUs are tracked here". Default empty so callers that don't care about
    # the m2m don't have to pass it.
    products: List[Product] = field(default_factory=list)
    # NOTE: substitutes are a self-referential m2m stored in the
    # StockItemSubstitute table and accessed directly (the generic repository
    # can't self-join an entity to itself), so there's no relationship field
    # here. See features/stock_items/add_substitute.py and get_stock_item_detail.

    class Fields(BaseEntity.Fields):
        EXPIRY_DATE = "expiry_date"
        IS_ESSENTIAL = "is_essential"
        IS_OPEN = "is_open"
        NAME = "name"
        NOTES = "notes"
        OPENED_ON = "opened_on"
        PRODUCTS = "products"
        STOCK_GROUP = "stock_group"
        STOCK_LEVEL = "stock_level"
        STOCK_LEVEL_LAST_UPDATED = "stock_level_last_updated"
        STOCK_LOCATION = "stock_location"
        STOCKTAKE_ALERTS_ARE_ENABLED = "stocktake_alerts_are_enabled"
        LAST_CHECKED_AT = "last_checked_at"
        SNOOZED_UNTIL = "snoozed_until"
        USUAL_STORE_ID = "usual_store_id"
        NUTRITION_FOOD_ID = "nutrition_food_id"
        NUTRITION_IGNORED = "nutrition_ignored"
