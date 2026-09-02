"""Dashboard summary endpoint.

Returns a single aggregated payload so the dashboard page renders with one
network round-trip instead of one-per-card. Each card on the frontend pulls
its data out of this single response.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.stock_status import StockStatus, level_for_status
from dora_api.features.app_settings.clock import household_today
from dora_api.features.recipes.get_recipes import load_recipe_cookability
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class StockItemSummary:
    total: int
    out_of_stock: int
    low_stock: int


@dataclass(frozen=True, slots=True)
class ShoppingListSummary:
    # Count of active (non-done) lists. The dashboard's primary-list card
    # surfaces this as its "+N other active lists" footer link.
    #
    # FU-826: `total_items` (unticked lines across every list) was dropped —
    # nothing in the app read it. It was also the subject of FU-767, a bug
    # report about the count being wrong because it had no join to list status,
    # so unticked leftovers on finished lists inflated it forever. The honest
    # fix for a field no surface renders is deletion, not a status join; that
    # retires FU-767 too.
    total: int


@dataclass(frozen=True, slots=True)
class RecipeSummary:
    # FU-826: `favourites`, `cookable_count` and `needs_linking_count` were all
    # dropped — no consumer. They were shipped for counter cards that
    # IMPL_PLAN_DASHBOARD_REBUILD Phase 1 deleted (§2.6, "raw totals answer no
    # question the user has"); the cards went, the payload behind them did not.
    #
    # `total` survives because AboutSettings' "at a glance" block renders it,
    # and the dashboard's hero line reads it for the "your recipe book's empty"
    # nudge.
    #
    # NOTE: the cookability map is still computed below — the per-entry
    # `missing_count` on each upcoming meal-plan entry needs it. Only the two
    # whole-collection *sums* are gone.
    total: int


@dataclass(frozen=True, slots=True)
class UpcomingMealPlanEntry:
    recipe_id: UUID
    recipe_name: str
    scheduled_for: date
    slot: str
    servings: int
    # cookability flag for the dashboard's "Next to cook" card.
    # Derived from the shared cookability map (R-003), so the rule lives in one
    # place. `None` for empty recipes (no ingredients to evaluate) OR for
    # recipes with unlinked required ingredients (Chunk 4 tri-state); the
    # SPA distinguishes via ``unlinked_ingredient_count`` — non-zero means
    # "needs linking" (not "empty recipe"). Otherwise the count of missing
    # ingredients (0 = ready to cook).
    missing_count: Optional[int]
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — count of the recipe's required
    # ingredients that have no ``stock_item_id``. Non-zero ⇒ this entry
    # renders "N need linking" in the dashboard, not "No ingredients".
    unlinked_ingredient_count: int = 0


@dataclass(frozen=True, slots=True)
class MealPlanSummary:
    # First 7 upcoming entries, sorted by date. The frontend uses this both
    # for the "next up" callout (entries[0]) and the 7-day strip.
    upcoming_entries: List[UpcomingMealPlanEntry] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DashboardSummaryDto:
    # FU-826 — `products` and `meals` were whole sub-objects nothing rendered.
    # `products.total` and `meals.{total_definitions,total_in_stock}` existed for
    # counter cards cut in the dashboard rebuild's Phase 1; the two `meals`
    # figures were also a pair of dedicated aggregate queries run on every
    # dashboard load, for nobody.
    stock_items: StockItemSummary
    shopping_lists: ShoppingListSummary
    recipes: RecipeSummary
    meal_plan: MealPlanSummary


class GetDashboardSummaryHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self) -> DashboardSummaryDto:
        # ── Stock items ───────────────────────────────────────────────────
        # Buckets are keyed to stock-status identity (sequence), not display
        # name — renaming a level in the UI must not change the counts.
        total_stock_items = self.repository.get(StockItem).count()
        all_levels = self.repository.get(StockLevel).all()
        out_level = level_for_status(all_levels, StockStatus.OUT_OF_STOCK)
        low_level = level_for_status(all_levels, StockStatus.LOW_STOCK)
        out_of_stock_id = out_level.id if out_level else None
        low_stock_id = low_level.id if low_level else None

        stock_level_field = EntityField(StockItem, "_stock_level_id")
        out_of_stock_count = (
            self.repository.get(StockItem).count(stock_level_field.eq(out_of_stock_id))
            if out_of_stock_id else 0
        )
        low_stock_count = (
            self.repository.get(StockItem).count(stock_level_field.eq(low_stock_id))
            if low_stock_id else 0
        )

        # ── Shopping lists ────────────────────────────────────────────────
        # "Active" = non-archived. The dashboard card surfaces what's
        # actually in flight; finished shops live on the lists page.
        status_field = EntityField(ShoppingList, ShoppingList.Fields.STATUS)
        total_lists = self.repository.get(ShoppingList).count(status_field.ne(SHOPPING_LIST_STATUS_DONE))

        # ── Recipes ───────────────────────────────────────────────────────
        total_recipes = self.repository.get(Recipe).count()
        # Cookability map via the shared query (same rule the recipe DTO and the
        # `?cookable` filter use — R-003). Still needed: each upcoming meal-plan
        # entry below carries a per-recipe `missing_count` derived from it, which
        # is what drives the "Next to cook" card's ready / missing-N badge.
        # FU-826 removed only the two whole-collection sums built on top of it
        # (`cookable_count`, `needs_linking_count`), which nothing rendered.
        cookability = load_recipe_cookability(self.repository)

        # ── Meal plan: upcoming entries within the next week ──────────────
        # R-021 — "today" is the household-tz boundary, not server-local.
        _Today = household_today(self.repository)
        _Window = _Today + timedelta(days=7)
        upcoming_entries_entities = (
            self.repository
            .get(MealPlanEntry)
            .include(MealPlanEntry.Fields.RECIPE)
            .all(
                EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR)
                .between(_Today, _Window)
            )
        )
        upcoming_entries_entities.sort(key=lambda e: (e.scheduled_for, e.slot))
        # reuse the cookability map already computed for the recipe
        # summary above so we don't load ingredients twice.
        # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4: an upcoming meal-plan entry
        # whose recipe has ANY unlinked required ingredient reads
        # missing_count as null (unknown) — the SPA renders the
        # calendar chip dimmed rather than "N missing", same neutral
        # state as RecipeCard.
        upcoming_entries_dto: List[UpcomingMealPlanEntry] = []
        for e in upcoming_entries_entities:
            missing, ingredient_count, unlinked = cookability.get(e.recipe.id, (0, 0, 0))
            if ingredient_count == 0 or unlinked > 0:
                _missing_for_entry = None
            else:
                _missing_for_entry = missing
            upcoming_entries_dto.append(UpcomingMealPlanEntry(
                recipe_id = e.recipe.id,
                recipe_name = e.recipe.name,
                scheduled_for = e.scheduled_for,
                slot = e.slot,
                servings = e.servings,
                missing_count = _missing_for_entry,
                unlinked_ingredient_count = unlinked,
            ))

        return DashboardSummaryDto(
            stock_items = StockItemSummary(
                total = total_stock_items,
                out_of_stock = out_of_stock_count,
                low_stock = low_stock_count,
            ),
            shopping_lists = ShoppingListSummary(total = total_lists),
            recipes = RecipeSummary(total = total_recipes),
            meal_plan = MealPlanSummary(
                upcoming_entries = upcoming_entries_dto,
            ),
        )

@DASHBOARD_ROUTER.route("/summary")
def get_dashboard_summary():
    _Logger = logging.getLogger(__name__)
    _Handler = GetDashboardSummaryHandler(SqlAlchemyRepository())
    _Summary = _Handler.handle()
    _Logger.debug(
        "Dashboard summary: %d stock items (%d low, %d out)",
        _Summary.stock_items.total,
        _Summary.stock_items.low_stock,
        _Summary.stock_items.out_of_stock,
    )
    return ok(_Summary)
