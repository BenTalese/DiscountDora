"""Rich single-stock-item endpoint.

The list endpoint at `GET /api/stock-items` returns a compact DTO suitable
for the overview grid. This one is used by the detail page and includes:
  * everything on the list DTO
  * notes, stocktake_alerts_are_enabled (Mute)
  * the location name and stock-level name (so the page doesn't need to
    cross-reference lookups)
  * linked products with their store + current offer info
  * linked recipes (just id + name) — derived via the RecipeIngredient join
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DONE, ShoppingList, ShoppingListLine,
)
from dora_api.domain.entities.preferred_buy import PreferredBuy
from dora_api.domain.entities.cook_event import CookEvent
from dora_api.domain.entities.store import Store
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_expiry_event import StockItemExpiryEvent
from dora_api.domain.entities.stock_item_price_observation import StockItemPriceObservation
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.stock_status import get_stock_item_unit_cost_at
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.features.stock_items.your_prices import build_your_prices_for_item
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class LinkedProductDto:
    product_id: UUID
    name: str
    brand: str | None
    store_id: UUID
    store_name: str
    # producer's SKU code, retained verbatim.
    merchant_stockcode: str | None
    size: str | None
    web_url: str | None
    price_now: float | None
    price_was: float | None


@dataclass(frozen=True, slots=True)
class LinkedRecipeDto:
    recipe_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class StockItemBarcodeDto:
    """FU-056 — one row in the stock-item-detail Barcodes section.

    `source` distinguishes two origins of the same lookup result:

    * `direct` — the user explicitly registered this EAN against this
      stock item (the Barcode row's `stock_item_id` points here).
    * `via_product` — the EAN is a linked Product's catalogue code,
      reaching this stock item through `StockItemProduct`. The SPA
      renders these read-only on the stock-item surface; editing
      lives on the Product.

    `product_id` / `product_name` are set only for `via_product` rows.
    """
    barcode_id: UUID
    barcode: str
    source: str   # 'direct' | 'via_product'
    product_id: UUID | None
    product_name: str | None


@dataclass(frozen=True, slots=True)
class SubstituteDto:
    stock_item_id: UUID
    name: str
    stock_level_id: UUID | None
    stock_level_name: str | None
    # free-text hint. NULL when the user didn't set one.
    notes: str | None
    # optional structured ratio "qty_in of THIS item → qty_out of
    # the substitute". The four fields are stored in the canonical pair's
    # A→B direction; the handler inverts here so consumers always see the
    # ratio from the viewing item's perspective. All four are None or all
    # four are set (DB CHECK enforces it).
    ratio_quantity_in: float | None
    ratio_unit_in: str | None
    ratio_quantity_out: float | None
    ratio_unit_out: str | None


@dataclass(frozen=True, slots=True)
class LevelChangeDto:
    changed_at: datetime
    stock_level_id: UUID | None
    stock_level_name: str | None


# lifecycle timeline inputs. The frontend merges these
# with `level_history` (and synthesises open/checked rows from current
# state) into a single date-sorted q-timeline. Keeping them as separate
# typed lists rather than a pre-merged union lets the client style each
# event kind on its own without re-parsing strings.
@dataclass(frozen=True, slots=True)
class WasteEventDto:
    occurred_at: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class ListAddEventDto:
    added_at: datetime
    added_via: str
    shopping_list_id: UUID
    shopping_list_name: str


# History tab — the "you actually bought this" surface. Projected from
# ShoppingListLine rows on lists with `status='done'` where the line
# was ticked at Finish. Purely read-side: no new table, no dedicated
# write path — the /finish handler already stamps
# `actual_unit_price` + `purchased_store_id` on the line, plus the
# parent list's `completed_at` gives us the "when." Store name is
# resolved server-side so the SPA renders a string, not the FK.
@dataclass(frozen=True, slots=True)
class PurchaseEventDto:
    occurred_at: datetime
    quantity: int
    actual_unit_price: float | None
    store_id: UUID | None
    store_name: str | None
    shopping_list_id: UUID
    shopping_list_name: str


# History tab — the "used in a recipe you actually cooked" surface.
# Written by POST /recipes/<id>/cook (see cook_recipe.py); projected
# here by walking the item's linked-recipe universe and pulling every
# CookEvent for those recipes. `meals_cooked` gives the SPA an
# optional badge ("Used 3× in Pasta Bake") on batch cooks.
@dataclass(frozen=True, slots=True)
class CookEventDto:
    occurred_at: datetime
    recipe_id: UUID | None
    recipe_name: str
    meals_cooked: int


# History tab — expiry-date change trail (set / pushed / cleared).
# Written by create_stock_item + update_stock_item on every date
# transition; the classifier assigns `kind` and (for pushes) a
# `delta_days`. Repeat pushes surface a "kept pushing this back"
# pattern the user can act on.
@dataclass(frozen=True, slots=True)
class ExpiryEventDto:
    occurred_at: datetime
    kind: str
    previous_expiry_date: date | None
    new_expiry_date: date | None
    delta_days: int | None


# free-text "what I actually buy" reminders (PROPOSAL_PRODUCTS_AS_OVERLAY
# §3.1). Everyday-user construct, separate from the Product overlay; always
# present, never gated by the products/money features.
@dataclass(frozen=True, slots=True)
class PreferredBuyDto:
    preferred_buy_id: UUID
    label: str


# folded shape (A1) `{total_price, total_measure, unit}`
# plus the A2 store surfacing ("Last seen at Coles") and A4-revised FK
# provenance ("from <list>" when harvested from a shopping line at /finish).
# Money-gated at the UI surfaces, not at the handler.
@dataclass(frozen=True, slots=True)
class PriceObservationDto:
    observation_id: UUID
    total_price: float
    total_measure: float
    unit: str
    observed_at: datetime
    # A2 — optional store; resolved name for the chip on the detail page.
    store_id: UUID | None
    store_name: str | None
    # A4 revised — provenance FK (LC-4: provenance only, not a sync link).
    # `shopping_list_name` is a small human label resolved server-side
    # ("Wed's shopping list") so the client renders a string, not the FK.
    shopping_list_line_id: UUID | None
    shopping_list_name: str | None
    # Multipack metadata (FU-227 follow-up). When set, the obs list shows
    # "4 × 125g" instead of "500g flat"; math is unaffected.
    pack_count: int | None


# what the PriceEntry widget seeds itself with on open (F2 —
# "every field prefilled from latest observation so the common case is confirm
# one number"). Resolved server-side so the SPA renders a label, not derived
# logic. `source_label` is a short human string ("from your last log",
# "from your last receipt") — the widget shows it as a chip.
@dataclass(frozen=True, slots=True)
class PriceEntryPrefillDto:
    total_price: float
    total_measure: float
    unit: str
    store_id: UUID | None
    store_name: str | None
    source_label: str


# populated by `build_your_prices_for_item`. R-003: every
# field is server-derived. `offers_sidecar` (LC-2) is a separate UI region
# in the widget — "Current shelf prices: $X at Y" — and never folded into
# the median.
@dataclass(frozen=True, slots=True)
class OfferSidecarDto:
    store_name: str
    price_per_unit: float
    unit: str


@dataclass(frozen=True, slots=True)
class YourPricesDto:
    baseline: float | None
    baseline_unit: str | None
    current: float | None
    above_baseline: bool
    sample_count: int
    last_observed_at: datetime | None
    last_seen_store_name: str | None
    offers_sidecar: list[OfferSidecarDto]


@dataclass(frozen=True, slots=True)
class LinkedNutritionFoodDto:
    """The nutrition-catalogue food a stock item is linked to. Carries its
    source so the detail page can say where the numbers came from — the same
    honesty the lookup picker applies (P3)."""
    nutrition_food_id: UUID
    name: str
    brand: str | None
    source: str
    source_label: str
    kcal_per_100g: float | None
    protein_g_per_100g: float | None
    carbs_g_per_100g: float | None
    fat_g_per_100g: float | None


@dataclass(frozen=True, slots=True)
class StockItemDetailDto:
    stock_item_id: UUID
    name: str
    notes: str | None
    stocktake_alerts_are_enabled: bool
    stock_level_id: UUID | None
    stock_level_name: str | None
    stock_location_id: UUID | None
    stock_location_name: str | None
    stock_location_breadcrumb: List[str]
    stock_group_id: UUID | None
    stock_group_name: str | None
    stock_level_last_updated: datetime
    expiry_date: date | None
    is_open: bool
    opened_on: date | None
    is_essential: bool
    # usual store hint (nullable). Surfaced as a small picker on the
    # stock-item detail; drives the shopping-list grouping
    # (PROPOSAL_PRODUCTS_AS_OVERLAY §3.3) when set.
    usual_store_id: UUID | None
    usual_store_name: str | None
    products: List[LinkedProductDto]
    recipes: List[LinkedRecipeDto]
    substitutes: List[SubstituteDto]
    level_history: List[LevelChangeDto]
    # last-N lifecycle inputs for the History tab. Capped
    # at the handler so the JSON stays light on busy items; older history
    # is intentionally not surfaced here (it lives in the waste-insights /
    # spend reports surfaces instead).
    waste_events: List[WasteEventDto] = field(default_factory=list)
    recent_list_adds: List[ListAddEventDto] = field(default_factory=list)
    # 2026-06-30 — three new history-tab feeds. Capped per-kind at
    # `HISTORY_PER_KIND_CAP` (see below); older rows are counted, not
    # rendered.
    purchase_events: List[PurchaseEventDto] = field(default_factory=list)
    cook_events: List[CookEventDto] = field(default_factory=list)
    expiry_events: List[ExpiryEventDto] = field(default_factory=list)
    # 2026-06-30 — total number of history events that exist for this
    # item but were NOT included in the response because they fell past
    # the per-kind cap. Summed across every event kind (level_history +
    # waste + list-adds + purchase + cook + expiry). The SPA renders a
    # single honest footer — "N older events not shown" — instead of
    # silently truncating.
    history_older_count: int = 0
    # free-text "what I buy" reminders (always present; not gated).
    preferred_buys: List[PreferredBuyDto] = field(default_factory=list)
    # price observations + the server-derived per-unit cost (the
    # client never divides — R-003). Money-gated at the UI, not here.
    price_observations: List[PriceObservationDto] = field(default_factory=list)
    unit_cost: float | None = None
    # what the shared PriceEntry widget should seed itself
    # with when opened (F2). Null when no prior observation exists. Resolved
    # server-side so the source label ("from your last log") stays consistent.
    price_entry_prefill: PriceEntryPrefillDto | None = None
    # None until enough price data has accrued — the widget renders the
    # "Not enough price data yet" state in that case.
    your_prices: YourPricesDto | None = None
    # every barcode that resolves to this stock item, whether
    # registered directly (source=='direct') or via a linked Product
    # (source=='via_product'). Always present; the SPA gates the surface
    # on `features.scanning`.
    barcodes: List['StockItemBarcodeDto'] = field(default_factory=list)
    # Last-checked timestamp — surfaced as a synthetic "Checked" entry in
    # the timeline whenever it differs from the most recent level change.
    last_checked_at: datetime | None = None
    # Nutrition complex-mode: the food this item is linked to, if any. Sent as
    # a resolved object rather than a bare id so the detail page can render the
    # link (name + source + per-100g) without a second round-trip. Null when
    # unlinked — which is the honest default, since a link only ever exists
    # because a human confirmed one.
    nutrition_food: 'LinkedNutritionFoodDto | None' = None


# 2026-06-30 — one number, one policy. Every event-kind projection
# below caps at this many rows (newest first); the leftover count is
# summed into `history_older_count` on the DTO so the SPA can render a
# single honest "N older events not shown" footer.
HISTORY_PER_KIND_CAP = 50


class GetStockItemDetailHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, stock_item_id: UUID) -> StockItemDetailDto | None:
        _StockItem: StockItem | None = (
            self.repository
            .get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .include(StockItem.Fields.STOCK_LOCATION)
            .include(StockItem.Fields.STOCK_GROUP)
            # store and current_offer are siblings on Product, so each needs
            # its own include("products") branch — chaining then_include would
            # try to resolve current_offer on Store.
            .include(StockItem.Fields.PRODUCTS)
                .then_include("store")
            .include(StockItem.Fields.PRODUCTS)
                .then_include("current_offer")
            .one(EntityField(StockItem, "id").eq(stock_item_id))
        )
        if not _StockItem:
            return None

        # Recipes that use this stock item — pulled from the ingredient join.
        # We could do this in one big query joining Recipe → RecipeIngredient
        # → StockItem; doing it in two cheap queries keeps the recipe column
        # selection simple and is plenty fast at any realistic scale.
        # `_recipe_id` and `_stock_item_id` are the underscore-prefixed mapper
        # properties on RecipeIngredient (see table_mappings.py) — that naming
        # keeps the FK columns out of verify_mappings.
        _Session = self.repository.session
        _IngredientRecipeIds = list(_Session.execute(
            select(RecipeIngredient._recipe_id)
            .where(RecipeIngredient._stock_item_id == stock_item_id)
            .distinct()
        ).scalars())
        _LinkedRecipes: List[LinkedRecipeDto] = []
        if _IngredientRecipeIds:
            _Recipes = list(_Session.execute(
                select(Recipe).where(Recipe.id.in_(_IngredientRecipeIds))
            ).scalars())
            _Recipes.sort(key=lambda r: r.name.lower())
            _LinkedRecipes = [
                LinkedRecipeDto(recipe_id=r.id, name=r.name) for r in _Recipes
            ]

        _LinkedProducts = sorted(
            (
                LinkedProductDto(
                    product_id = p.id,
                    name = p.name,
                    brand = p.brand,
                    store_id = p.store.id,
                    store_name = p.store.name,
                    merchant_stockcode = p.merchant_stockcode,
                    size = p.size,
                    web_url = p.web_url,
                    price_now = p.current_offer.price_now if p.current_offer else None,
                    price_was = p.current_offer.price_was if p.current_offer else None,
                )
                for p in (_StockItem.products or [])
            ),
            key=lambda d: (d.store_name.lower(), d.name.lower()),
        )

        # Walk the location's parent chain so the detail page can show
        # "Pantry > Middle shelf > Left side" without a second request.
        _Breadcrumb: List[str] = []
        if _StockItem.stock_location is not None:
            _LocationLookup = {
                loc.id: loc for loc in self.repository.get(StockLocation).all()
            }
            _Cursor: StockLocation | None = _StockItem.stock_location
            _Safety = 16
            while _Cursor is not None and _Safety > 0:
                _Breadcrumb.append(_Cursor.name)
                _Cursor = (
                    _LocationLookup.get(_Cursor.parent_id) if _Cursor.parent_id else None
                )
                _Safety -= 1
            _Breadcrumb.reverse()

        # Substitutes — read straight from the association table (the generic
        # repository can't self-join StockItem). Level names come from a small
        # lookup so we avoid a join.
        _LevelLookup = {lvl.id: lvl.name for lvl in self.repository.get(StockLevel).all()}
        # Undirected pairs: the "other side" is whichever column is *not*
        # the current item. FU-034: we now also need the per-pair `notes`
        # and ratio columns, and the ratio must be **inverted** when we're
        # viewing the pair from the B side so the consumer always sees
        # `qty_in/unit_in` as "this item" and `qty_out/unit_out` as "the
        # substitute".
        _Assoc = db.metadata.tables["StockItemSubstitute"]
        _AsA = _Session.execute(
            select(
                _Assoc.c.stock_item_b_id,
                _Assoc.c.notes,
                _Assoc.c.ratio_quantity_in,
                _Assoc.c.ratio_unit_in,
                _Assoc.c.ratio_quantity_out,
                _Assoc.c.ratio_unit_out,
            ).where(_Assoc.c.stock_item_a_id == stock_item_id)
        ).all()
        _AsB = _Session.execute(
            select(
                _Assoc.c.stock_item_a_id,
                _Assoc.c.notes,
                # Swap the in/out pair so we display from B's side.
                _Assoc.c.ratio_quantity_out.label("ratio_quantity_in"),
                _Assoc.c.ratio_unit_out.label("ratio_unit_in"),
                _Assoc.c.ratio_quantity_in.label("ratio_quantity_out"),
                _Assoc.c.ratio_unit_in.label("ratio_unit_out"),
            ).where(_Assoc.c.stock_item_b_id == stock_item_id)
        ).all()
        # other_id → metadata. If both directions returned the same row
        # (shouldn't happen with canonical storage), the later wins; both
        # are equivalent semantically.
        _MetaByOther: dict = {}
        for row in list(_AsA) + list(_AsB):
            _MetaByOther[row[0]] = {
                "notes": row[1],
                "ratio_quantity_in": row[2],
                "ratio_unit_in": row[3],
                "ratio_quantity_out": row[4],
                "ratio_unit_out": row[5],
            }
        _SubIds = list(_MetaByOther.keys())
        _Substitutes: List[SubstituteDto] = []
        if _SubIds:
            _SubItems = list(_Session.execute(
                select(StockItem).where(StockItem.id.in_(_SubIds))
            ).scalars())
            _Substitutes = sorted(
                (
                    SubstituteDto(
                        stock_item_id = s.id,
                        name = s.name,
                        stock_level_id = s._stock_level_id,
                        stock_level_name = _LevelLookup.get(s._stock_level_id),
                        notes = _MetaByOther[s.id]["notes"],
                        ratio_quantity_in = _MetaByOther[s.id]["ratio_quantity_in"],
                        ratio_unit_in = _MetaByOther[s.id]["ratio_unit_in"],
                        ratio_quantity_out = _MetaByOther[s.id]["ratio_quantity_out"],
                        ratio_unit_out = _MetaByOther[s.id]["ratio_unit_out"],
                    )
                    for s in _SubItems
                ),
                key=lambda d: d.name.lower(),
            )

        # Running tally of every event dropped past the per-kind cap
        # across every history feed. Reported as `history_older_count`
        # on the DTO so the SPA can show a single truncation footer.
        _HistoryOlderCount = 0

        # Level-change history — newest first, capped so the page stays light.
        _Changes = self.repository.get(StockLevelChange).all(
            EntityField(StockLevelChange, StockLevelChange.Fields.STOCK_ITEM_ID).eq(stock_item_id)
        )
        _Changes.sort(key=lambda c: c.changed_at, reverse=True)
        _HistoryOlderCount += max(0, len(_Changes) - HISTORY_PER_KIND_CAP)
        _LevelHistory = [
            LevelChangeDto(
                changed_at = c.changed_at,
                stock_level_id = c.stock_level_id,
                stock_level_name = c.stock_level_name,
            )
            for c in _Changes[:HISTORY_PER_KIND_CAP]
        ]

        # lifecycle inputs (read-only, capped).
        # Waste events: append-only log (P2-06); newest first.
        _Wastes = self.repository.get(StockItemWasteEvent).all(
            EntityField(StockItemWasteEvent, StockItemWasteEvent.Fields.STOCK_ITEM_ID).eq(stock_item_id)
        )
        _Wastes.sort(key=lambda w: w.occurred_at, reverse=True)
        _HistoryOlderCount += max(0, len(_Wastes) - HISTORY_PER_KIND_CAP)
        _WasteEvents = [
            WasteEventDto(
                occurred_at = w.occurred_at,
                reason = w.reason,
            )
            for w in _Wastes[:HISTORY_PER_KIND_CAP]
        ]

        # Past list-adds: every line for this stock item that has an
        # added_at stamp. Lines on done/archived lists are intentionally
        # included — the timeline is about the *item's* history, not the
        # current cart. Look up list names from a tiny cache to avoid
        # N+1 SELECTs. Filter at the field; sort + cap on the result.
        _Lines = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID).eq(stock_item_id)
        )
        _Lines = [l for l in _Lines if l.added_at is not None]
        _Lines.sort(key=lambda l: l.added_at, reverse=True)
        _HistoryOlderCount += max(0, len(_Lines) - HISTORY_PER_KIND_CAP)
        _Lines = _Lines[:HISTORY_PER_KIND_CAP]
        _ListAdds: List[ListAddEventDto] = []
        if _Lines:
            _ListIds = {l.shopping_list_id for l in _Lines}
            _Lists = list(_Session.execute(
                select(ShoppingList).where(ShoppingList.id.in_(_ListIds))
            ).scalars())
            _ListNameLookup = {lst.id: lst.display_name for lst in _Lists}
            _ListAdds = [
                ListAddEventDto(
                    added_at = l.added_at,
                    added_via = l.added_via,
                    shopping_list_id = l.shopping_list_id,
                    shopping_list_name = _ListNameLookup.get(l.shopping_list_id, '(deleted list)'),
                )
                for l in _Lines
            ]

        # ── Purchase events (2026-06-30) ─────────────────────────────
        # "You actually bought this on <date> at <store>." Pulled from
        # every ShoppingListLine for this item where the parent list
        # is `done` AND the line was ticked at Finish. The parent
        # list's `completed_at` gives the "when" (a line has no
        # per-tick timestamp; the list-level stamp is the closest
        # proxy). Reuses the ShoppingList name cache built above so
        # we don't re-hit the DB.
        _PurchaseEvents: List[PurchaseEventDto] = []
        _AllLinesForItem = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID).eq(stock_item_id)
        )
        _BoughtLines = [
            l for l in _AllLinesForItem
            if l.is_ticked
        ]
        if _BoughtLines:
            # Load parent lists for status + completed_at. Separate hit
            # from the recent-list-adds branch's name-only cache because
            # here we need the full row (status/completed_at/name).
            _BoughtListIds = {l.shopping_list_id for l in _BoughtLines}
            _AllLists = list(_Session.execute(
                select(ShoppingList).where(ShoppingList.id.in_(_BoughtListIds))
            ).scalars())
            _ListForId = {lst.id: lst for lst in _AllLists}
            # Resolve store names in one hit for the union of purchased_store_ids.
            _StoreIds = {
                l.purchased_store_id for l in _BoughtLines
                if l.purchased_store_id is not None
            }
            _StoreNameLookup: dict[UUID, str] = {}
            if _StoreIds:
                _Stores = list(_Session.execute(
                    select(Store).where(Store.id.in_(_StoreIds))
                ).scalars())
                _StoreNameLookup = {s.id: s.name for s in _Stores}

            _Purchases_raw = []
            for l in _BoughtLines:
                lst = _ListForId.get(l.shopping_list_id)
                # Only surface lines on genuinely-finished lists — a
                # ticked line on an in-flight list means the user is
                # mid-shop, not that they've bought yet.
                if lst is None or lst.status != SHOPPING_LIST_STATUS_DONE:
                    continue
                if lst.completed_at is None:
                    continue
                _Purchases_raw.append((lst, l))
            _Purchases_raw.sort(key=lambda pair: pair[0].completed_at, reverse=True)
            _HistoryOlderCount += max(0, len(_Purchases_raw) - HISTORY_PER_KIND_CAP)
            _Purchases_raw = _Purchases_raw[:HISTORY_PER_KIND_CAP]
            _PurchaseEvents = [
                PurchaseEventDto(
                    occurred_at = lst.completed_at,
                    quantity = l.quantity,
                    actual_unit_price = l.actual_unit_price,
                    store_id = l.purchased_store_id,
                    store_name = (
                        _StoreNameLookup.get(l.purchased_store_id)
                        if l.purchased_store_id is not None else None
                    ),
                    shopping_list_id = lst.id,
                    shopping_list_name = lst.display_name,
                )
                for lst, l in _Purchases_raw
            ]

        # ── Cook events (2026-06-30) ─────────────────────────────────
        # "You cooked a recipe that uses this ingredient." Universe of
        # recipes is exactly the linked-recipes set already computed
        # above (any recipe with an ingredient referencing this stock
        # item). Iterating CookEvent by `recipe_id IN (…)` uses the
        # `cook_event_recipe_id` index so this stays cheap even on
        # heavy cooks. Cap at 20.
        _CookEvents: List[CookEventDto] = []
        if _IngredientRecipeIds:
            _CookRows = list(_Session.execute(
                select(CookEvent).where(
                    CookEvent.recipe_id.in_(_IngredientRecipeIds)
                )
            ).scalars())
            _CookRows.sort(key=lambda e: e.occurred_at, reverse=True)
            _HistoryOlderCount += max(0, len(_CookRows) - HISTORY_PER_KIND_CAP)
            _CookEvents = [
                CookEventDto(
                    occurred_at = e.occurred_at,
                    recipe_id = e.recipe_id,
                    recipe_name = e.recipe_name,
                    meals_cooked = e.meals_cooked,
                )
                for e in _CookRows[:HISTORY_PER_KIND_CAP]
            ]

        # ── Expiry events (2026-06-30) ───────────────────────────────
        # Every set / pushed / cleared transition for this item.
        # Newest first, capped at 20.
        _ExpiryRows = self.repository.get(StockItemExpiryEvent).all(
            EntityField(
                StockItemExpiryEvent,
                StockItemExpiryEvent.Fields.STOCK_ITEM_ID,
            ).eq(stock_item_id)
        )
        _ExpiryRows.sort(key=lambda e: e.occurred_at, reverse=True)
        _HistoryOlderCount += max(0, len(_ExpiryRows) - HISTORY_PER_KIND_CAP)
        _ExpiryEvents = [
            ExpiryEventDto(
                occurred_at = e.occurred_at,
                kind = e.kind,
                previous_expiry_date = e.previous_expiry_date,
                new_expiry_date = e.new_expiry_date,
                delta_days = e.delta_days,
            )
            for e in _ExpiryRows[:HISTORY_PER_KIND_CAP]
        ]

        # free-text preferred buys for this item. FU-225 dropped
        # the `position` column and the manual reorder UI; sort alphabetically
        # (case-insensitive) for a stable, predictable order matching the SPA.
        _PreferredBuys = sorted(
            (
                PreferredBuyDto(
                    preferred_buy_id = pb.id,
                    label = pb.label,
                )
                for pb in self.repository.get(PreferredBuy).all(
                    EntityField(PreferredBuy, PreferredBuy.Fields.STOCK_ITEM_ID).eq(stock_item_id)
                )
            ),
            key=lambda d: d.label.lower(),
        )

        # folded-shape observations (newest first) + the
        # single server-owned per-unit cost (R-003 — client never divides).
        # Provenance / store names resolved server-side so the SPA renders
        # strings, not raw FKs.
        _Observations = self.repository.get(StockItemPriceObservation).all(
            EntityField(
                StockItemPriceObservation,
                StockItemPriceObservation.Fields.STOCK_ITEM_ID,
            ).eq(stock_item_id)
        )
        _Observations.sort(key=lambda o: o.observed_at, reverse=True)

        # Resolve the small lookup pools once per request rather than N+1.
        _StoreNamesById: dict[UUID, str] = {}
        _ListNamesByLineId: dict[UUID, str] = {}
        _StoreIds = {o.store_id for o in _Observations if o.store_id is not None}
        if _StoreIds:
            from dora_api.domain.entities.store import Store as _StoreEntity
            for _s in self.repository.get(_StoreEntity).all(
                EntityField(_StoreEntity, "id").in_(list(_StoreIds))
            ):
                _StoreNamesById[_s.id] = _s.name
        _LineIds = {o.shopping_list_line_id for o in _Observations if o.shopping_list_line_id is not None}
        if _LineIds:
            from dora_api.domain.entities.shopping_list import ShoppingListLine as _Line, ShoppingList as _List
            _Lines = self.repository.get(_Line).all(
                EntityField(_Line, "id").in_(list(_LineIds))
            )
            _ListIds = {ln.shopping_list_id for ln in _Lines}
            _ListsById: dict[UUID, _List] = {}
            if _ListIds:
                for _sl in self.repository.get(_List).all(
                    EntityField(_List, "id").in_(list(_ListIds))
                ):
                    _ListsById[_sl.id] = _sl
            for ln in _Lines:
                sl = _ListsById.get(ln.shopping_list_id)
                if sl is not None:
                    _ListNamesByLineId[ln.id] = sl.name or "shopping list"

        _PriceObservations = [
            PriceObservationDto(
                observation_id = o.id,
                total_price = o.total_price,
                total_measure = o.total_measure,
                unit = o.unit,
                observed_at = o.observed_at,
                store_id = o.store_id,
                store_name = _StoreNamesById.get(o.store_id) if o.store_id is not None else None,
                shopping_list_line_id = o.shopping_list_line_id,
                shopping_list_name = _ListNamesByLineId.get(o.shopping_list_line_id) if o.shopping_list_line_id is not None else None,
                pack_count = o.pack_count,
            )
            for o in _Observations
        ]
        _UnitCost = get_stock_item_unit_cost_at(_Observations)

        # seed the PriceEntry widget from the most-recent
        # observation. The "source_label" line picks the right human framing
        # based on the FK (provenance) — manual entries say "your last log",
        # harvested entries say "your last receipt".
        _Prefill: PriceEntryPrefillDto | None = None
        if _Observations:
            _Latest = _Observations[0]  # already sorted newest-first above
            _SourceLabel = (
                "from your last receipt"
                if _Latest.shopping_list_line_id is not None
                else "from your last log"
            )
            _Prefill = PriceEntryPrefillDto(
                total_price=_Latest.total_price,
                total_measure=_Latest.total_measure,
                unit=_Latest.unit,
                store_id=_Latest.store_id,
                store_name=_StoreNamesById.get(_Latest.store_id) if _Latest.store_id is not None else None,
                source_label=_SourceLabel,
            )

        # server-derived baseline + signal (R-003: client
        # renders the booleans/numbers, never re-derives). Pure-function call
        # over already-loaded data via the repo.
        _YpRaw = build_your_prices_for_item(self.repository, stock_item_id)
        _YourPrices = YourPricesDto(
            baseline=_YpRaw.baseline,
            baseline_unit=_YpRaw.baseline_unit,
            current=_YpRaw.current,
            above_baseline=_YpRaw.above_baseline,
            sample_count=_YpRaw.sample_count,
            last_observed_at=_YpRaw.last_observed_at,
            last_seen_store_name=_YpRaw.last_seen_store_name,
            offers_sidecar=[
                OfferSidecarDto(
                    store_name=o.store_name,
                    price_per_unit=o.price_per_unit,
                    unit=o.unit,
                )
                for o in _YpRaw.offers_sidecar
            ],
        )

        # resolve the usual-store name for the detail DTO. Falls
        # back to None when the user hasn't picked one or the referenced
        # store has been deleted (the FK is SET NULL).
        _UsualStoreName: str | None = None
        if _StockItem.usual_store_id is not None:
            _UsualStore = self.repository.get(Store).by_id(_StockItem.usual_store_id)
            if _UsualStore is not None:
                _UsualStoreName = _UsualStore.name

        # gather every barcode that resolves to this stock item.
        # Two sources, merged + sorted by created_at descending:
        #   1. Direct registrations (Barcode.stock_item_id == this id)
        #   2. Indirect via a linked Product (StockItemProduct → Product
        #      → Barcode.product_id). Read-only on this surface; editing
        #      lives on the Product when the Products UI ships it.
        from dora_api.domain.entities.barcode import Barcode
        _Barcodes: List[StockItemBarcodeDto] = []
        _AllBarcodes = self.repository.get(Barcode).all()
        # _StockItem.products is a list of `Product` entities (m2m
        # selectin-loaded), so key off the entity id, not a "product_id"
        # field — that attribute lives on the StockItemProduct join row.
        _LinkedProductIds = {p.id for p in _StockItem.products or []}
        _ProductNamesById: dict = {
            p.id: getattr(p, "name", None) for p in (_StockItem.products or [])
        }
        for _Bc in _AllBarcodes:
            if _Bc.stock_item_id == stock_item_id:
                _Barcodes.append(StockItemBarcodeDto(
                    barcode_id=_Bc.id,
                    barcode=_Bc.barcode,
                    source="direct",
                    product_id=_Bc.product_id,
                    product_name=_ProductNamesById.get(_Bc.product_id),
                ))
            elif _Bc.product_id is not None and _Bc.product_id in _LinkedProductIds:
                _Barcodes.append(StockItemBarcodeDto(
                    barcode_id=_Bc.id,
                    barcode=_Bc.barcode,
                    source="via_product",
                    product_id=_Bc.product_id,
                    product_name=_ProductNamesById.get(_Bc.product_id),
                ))
        _Barcodes.sort(key=lambda b: (b.source != "direct", b.barcode))

        # Nutrition link. One targeted fetch, only when the item actually has
        # one — the FK is a plain UUID with no relationship object (R-032), so
        # nothing is loaded implicitly.
        _NutritionFood = None
        if getattr(_StockItem, "nutrition_food_id", None) is not None:
            from dora_api.domain.entities.nutrition_food import (
                NUTRITION_SOURCE_LABELS, NutritionFood,
            )
            _Food = self.repository.get(NutritionFood).by_id(_StockItem.nutrition_food_id)
            if _Food is not None:
                _NutritionFood = LinkedNutritionFoodDto(
                    nutrition_food_id = _Food.id,
                    name = _Food.name,
                    brand = _Food.brand,
                    source = _Food.source,
                    source_label = NUTRITION_SOURCE_LABELS.get(_Food.source, _Food.source),
                    kcal_per_100g = _Food.kcal_per_100g,
                    protein_g_per_100g = _Food.protein_g_per_100g,
                    carbs_g_per_100g = _Food.carbs_g_per_100g,
                    fat_g_per_100g = _Food.fat_g_per_100g,
                )

        return StockItemDetailDto(
            stock_item_id = _StockItem.id,
            name = _StockItem.name,
            notes = _StockItem.notes,
            stocktake_alerts_are_enabled = _StockItem.stocktake_alerts_are_enabled,
            stock_level_id = _StockItem.stock_level.id if _StockItem.stock_level else None,
            stock_level_name = _StockItem.stock_level.name if _StockItem.stock_level else None,
            stock_location_id = _StockItem.stock_location.id if _StockItem.stock_location else None,
            stock_location_name = _StockItem.stock_location.name if _StockItem.stock_location else None,
            stock_location_breadcrumb = _Breadcrumb,
            stock_group_id = _StockItem.stock_group.id if _StockItem.stock_group else None,
            stock_group_name = _StockItem.stock_group.name if _StockItem.stock_group else None,
            stock_level_last_updated = _StockItem.stock_level_last_updated,
            expiry_date = _StockItem.expiry_date,
            is_open = bool(_StockItem.is_open),
            opened_on = _StockItem.opened_on,
            is_essential = bool(_StockItem.is_essential),
            usual_store_id = _StockItem.usual_store_id,
            usual_store_name = _UsualStoreName,
            products = _LinkedProducts,
            recipes = _LinkedRecipes,
            substitutes = _Substitutes,
            waste_events = _WasteEvents,
            recent_list_adds = _ListAdds,
            purchase_events = _PurchaseEvents,
            cook_events = _CookEvents,
            expiry_events = _ExpiryEvents,
            history_older_count = _HistoryOlderCount,
            preferred_buys = _PreferredBuys,
            price_observations = _PriceObservations,
            unit_cost = _UnitCost,
            price_entry_prefill = _Prefill,
            your_prices = _YourPrices,
            barcodes = _Barcodes,

            last_checked_at = _StockItem.last_checked_at,
            nutrition_food = _NutritionFood,
            level_history = _LevelHistory,
        )


@STOCK_ITEM_ROUTER.route("<uuid:stock_item_id>/detail")
def get_stock_item_detail(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Detail = GetStockItemDetailHandler(SqlAlchemyRepository()).handle(stock_item_id)
    if _Detail is None:
        return not_found(StockItem.__name__, stock_item_id)
    _Logger.debug(
        "Stock item %s detail: %d products, %d recipes",
        stock_item_id, len(_Detail.products), len(_Detail.recipes),
    )
    return ok(_Detail)
