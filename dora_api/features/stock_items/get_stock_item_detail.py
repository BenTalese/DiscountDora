"""Rich single-stock-item endpoint.

The list endpoint at `GET /api/stock-items` returns a compact DTO suitable
for the overview grid. This one is used by the detail page and includes:
  * everything on the list DTO
  * notes, days_until_stocktake_alert, stocktake_alerts_are_enabled
  * the location name and stock-level name (so the page doesn't need to
    cross-reference stores)
  * linked merchant products with their current offer info
  * linked recipes (just id + name) — derived via the RecipeIngredient join
"""
import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.shopping_list import ShoppingList, ShoppingListLine
from dora_api.domain.entities.preferred_buy import PreferredBuy
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_price_observation import StockItemPriceObservation
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.stock_status import (effective_expiring_soon_window,
                                          get_stock_item_unit_cost_at)
from dora_api.features.locations.attention import reasons_for_item
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class LinkedProductDto:
    product_id: UUID
    name: str
    brand: str | None
    merchant_id: UUID
    merchant_name: str
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
class SubstituteDto:
    stock_item_id: UUID
    name: str
    stock_level_id: UUID | None
    stock_level_name: str | None


@dataclass(frozen=True, slots=True)
class LevelChangeDto:
    changed_at: datetime
    stock_level_id: UUID | None
    stock_level_name: str | None


# C-1b.5 / INV-7 — lifecycle timeline inputs. The frontend merges these
# with `level_history` (and synthesises open/checked rows from current
# state) into a single date-sorted q-timeline. Keeping them as separate
# typed lists rather than a pre-merged union lets the client style each
# event kind on its own without re-parsing strings.
@dataclass(frozen=True, slots=True)
class WasteEventDto:
    occurred_at: datetime
    reason: str
    quantity: int | None
    estimated_value: float | None
    note: str | None


@dataclass(frozen=True, slots=True)
class ListAddEventDto:
    added_at: datetime
    added_via: str
    shopping_list_id: UUID
    shopping_list_name: str


# FU-211 — free-text "what I actually buy" reminders (PROPOSAL_PRODUCTS_AS_OVERLAY
# §3.1). Everyday-user construct, separate from the Product overlay; always
# present, never gated by the products/money features.
@dataclass(frozen=True, slots=True)
class PreferredBuyDto:
    preferred_buy_id: UUID
    label: str
    position: int


# FU-213 — everyday "what this cost me" price points (money-gated at the UI).
@dataclass(frozen=True, slots=True)
class PriceObservationDto:
    observation_id: UUID
    price: float
    qty: float
    unit: str
    observed_at: datetime
    source: str


@dataclass(frozen=True, slots=True)
class StockItemDetailDto:
    stock_item_id: UUID
    name: str
    notes: str | None
    days_until_stocktake_alert: int
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
    is_flagged: bool
    auto_add_when_low: bool
    attention_score: int
    attention_reasons: dict
    products: List[LinkedProductDto]
    recipes: List[LinkedRecipeDto]
    substitutes: List[SubstituteDto]
    level_history: List[LevelChangeDto]
    # C-1b.5 / INV-7 — last-N lifecycle inputs for the History tab. Capped
    # at the handler so the JSON stays light on busy items; older history
    # is intentionally not surfaced here (it lives in the waste-insights /
    # spend reports surfaces instead).
    waste_events: List[WasteEventDto] = field(default_factory=list)
    recent_list_adds: List[ListAddEventDto] = field(default_factory=list)
    # FU-211 — free-text "what I buy" reminders (always present; not gated).
    preferred_buys: List[PreferredBuyDto] = field(default_factory=list)
    # FU-213 — price observations + the server-derived per-unit cost (the
    # client never divides — R-003). Money-gated at the UI, not here.
    price_observations: List[PriceObservationDto] = field(default_factory=list)
    unit_cost: float | None = None
    # Last-checked timestamp — surfaced as a synthetic "Checked" entry in
    # the timeline whenever it differs from the most recent level change.
    last_checked_at: datetime | None = None
    # C-1 Chunk 6 / FU-033 — image presence flag (own-image OR linked-
    # product image fallback). Bytes served via
    # `GET /stock-items/<id>/image`; never inlined in the JSON.
    has_image: bool = False
    # FU-125 — true only when the stock item carries its OWN uploaded
    # image (no fallback). Lets the detail page render "Add image" instead
    # of "Change image / Remove" when the preview is being served from a
    # linked product (there's nothing the user could "remove").
    has_own_image: bool = False


class GetStockItemDetailHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_item_id: UUID) -> StockItemDetailDto | None:
        _StockItem: StockItem | None = (
            self.repository
            .get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .include(StockItem.Fields.STOCK_LOCATION)
            .include(StockItem.Fields.STOCK_GROUP)
            # merchant and current_offer are siblings on Product, so each needs
            # its own include("products") branch — chaining then_include would
            # try to resolve current_offer on Merchant.
            .include(StockItem.Fields.PRODUCTS)
                .then_include("merchant")
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
                    merchant_id = p.merchant.id,
                    merchant_name = p.merchant.name,
                    merchant_stockcode = p.merchant_stockcode,
                    size = p.size,
                    web_url = p.web_url,
                    price_now = p.current_offer.price_now if p.current_offer else None,
                    price_was = p.current_offer.price_was if p.current_offer else None,
                )
                for p in (_StockItem.products or [])
            ),
            key=lambda d: (d.merchant_name.lower(), d.name.lower()),
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
        # the current item. We fetch each direction separately and union.
        _Assoc = db.metadata.tables["StockItemSubstitute"]
        _SubIds = set(_Session.execute(
            select(_Assoc.c.stock_item_b_id).where(_Assoc.c.stock_item_a_id == stock_item_id)
        ).scalars())
        _SubIds.update(_Session.execute(
            select(_Assoc.c.stock_item_a_id).where(_Assoc.c.stock_item_b_id == stock_item_id)
        ).scalars())
        _SubIds = list(_SubIds)
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
                    )
                    for s in _SubItems
                ),
                key=lambda d: d.name.lower(),
            )

        # Level-change history — newest first, capped so the page stays light.
        _Changes = self.repository.get(StockLevelChange).all(
            EntityField(StockLevelChange, StockLevelChange.Fields.STOCK_ITEM_ID).eq(stock_item_id)
        )
        _Changes.sort(key=lambda c: c.changed_at, reverse=True)
        _LevelHistory = [
            LevelChangeDto(
                changed_at = c.changed_at,
                stock_level_id = c.stock_level_id,
                stock_level_name = c.stock_level_name,
            )
            for c in _Changes[:20]
        ]

        # C-1b.5 / INV-7 — lifecycle inputs (read-only, capped).
        # Waste events: append-only log (P2-06); newest first.
        _Wastes = self.repository.get(StockItemWasteEvent).all(
            EntityField(StockItemWasteEvent, StockItemWasteEvent.Fields.STOCK_ITEM_ID).eq(stock_item_id)
        )
        _Wastes.sort(key=lambda w: w.occurred_at, reverse=True)
        _WasteEvents = [
            WasteEventDto(
                occurred_at = w.occurred_at,
                reason = w.reason,
                quantity = w.quantity,
                estimated_value = w.estimated_value,
                note = w.note,
            )
            for w in _Wastes[:20]
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
        _Lines = _Lines[:20]
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

        # FU-211 — free-text preferred buys for this item, ordered by position.
        _PreferredBuys = sorted(
            (
                PreferredBuyDto(
                    preferred_buy_id = pb.id,
                    label = pb.label,
                    position = pb.position,
                )
                for pb in self.repository.get(PreferredBuy).all(
                    EntityField(PreferredBuy, PreferredBuy.Fields.STOCK_ITEM_ID).eq(stock_item_id)
                )
            ),
            key=lambda d: d.position,
        )

        # FU-213 — price observations (newest first) + the single server-owned
        # per-unit cost derivation (R-003 — the client never divides).
        _Observations = self.repository.get(StockItemPriceObservation).all(
            EntityField(
                StockItemPriceObservation,
                StockItemPriceObservation.Fields.STOCK_ITEM_ID,
            ).eq(stock_item_id)
        )
        _Observations.sort(key=lambda o: o.observed_at, reverse=True)
        _PriceObservations = [
            PriceObservationDto(
                observation_id = o.id,
                price = o.price,
                qty = o.qty,
                unit = o.unit,
                observed_at = o.observed_at,
                source = o.source,
            )
            for o in _Observations
        ]
        _UnitCost = get_stock_item_unit_cost_at(_Observations)

        # C-9.2 — same household-configured expiring-soon window as the alerts
        # list + heatmap (R-003), falling back to the default.
        _Settings: List[AppSetting] = self.repository.get(AppSetting).all()
        _Window = effective_expiring_soon_window(_Settings[0] if _Settings else None)
        _Reasons = reasons_for_item(_StockItem, expiring_soon_window=_Window)

        return StockItemDetailDto(
            stock_item_id = _StockItem.id,
            name = _StockItem.name,
            notes = _StockItem.notes,
            days_until_stocktake_alert = _StockItem.days_until_stocktake_alert,
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
            is_flagged = bool(_StockItem.is_flagged),
            auto_add_when_low = bool(_StockItem.auto_add_when_low),
            attention_score = _Reasons.score(),
            attention_reasons = asdict(_Reasons),
            products = _LinkedProducts,
            recipes = _LinkedRecipes,
            substitutes = _Substitutes,
            waste_events = _WasteEvents,
            recent_list_adds = _ListAdds,
            preferred_buys = _PreferredBuys,
            price_observations = _PriceObservations,
            unit_cost = _UnitCost,
            last_checked_at = _StockItem.last_checked_at,
            level_history = _LevelHistory,
            # C-1 Chunk 6 / FU-033 — own-image OR any linked product image.
            # `_LinkedProducts` already loaded above; checks are cheap.
            has_image = bool(_StockItem.image) or any(
                bool(getattr(p, "image", None)) for p in (_StockItem.products or [])
            ),
            has_own_image = bool(_StockItem.image),
        )


@STOCK_ITEM_ROUTER.route("<stock_item_id>/detail")
def get_stock_item_detail(stock_item_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Detail = get_container().inject(GetStockItemDetailHandler).handle(stock_item_id)
    if _Detail is None:
        return not_found(StockItem.__name__, stock_item_id)
    _Logger.debug(
        "Stock item %s detail: %d products, %d recipes",
        stock_item_id, len(_Detail.products), len(_Detail.recipes),
    )
    return ok(_Detail)
