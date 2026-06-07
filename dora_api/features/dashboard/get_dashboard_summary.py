"""Dashboard summary endpoint.

Returns a single aggregated payload so the dashboard page renders with one
network round-trip instead of one-per-card. Each card on the frontend pulls
its data out of this single response.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List

from sqlalchemy import func, select

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.stock_status import StockStatus, level_for_status
from dora_api.features.recipes.get_recipes import load_recipe_cookability
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class StockItemSummary:
    total: int
    out_of_stock: int
    low_stock: int


@dataclass(frozen=True, slots=True)
class ShoppingListSummary:
    total: int
    total_items: int


@dataclass(frozen=True, slots=True)
class ProductSummary:
    total: int


@dataclass(frozen=True, slots=True)
class RecipeSummary:
    total: int
    favourites: int
    # Recipes you can cook right now: nothing missing AND at least one
    # ingredient (an empty recipe isn't something to "cook tonight"). Lets the
    # dashboard show the count without the client pulling + joining every recipe
    # against the whole pantry (state-ownership §3.3).
    cookable_count: int


@dataclass(frozen=True, slots=True)
class MealSummary:
    # Number of recipes that currently have meals in the pool, and the
    # total count of meals across all recipes. "Definitions" maps to
    # recipes-with-meals since Meal-as-its-own-entity is gone.
    total_definitions: int
    total_in_stock: int


@dataclass(frozen=True, slots=True)
class UpcomingMealPlanEntry:
    recipe_name: str
    scheduled_for: date
    slot: str
    servings: int


@dataclass(frozen=True, slots=True)
class MealPlanSummary:
    # First 7 upcoming entries, sorted by date. The frontend uses this both
    # for the "next up" callout (entries[0]) and the 7-day strip.
    upcoming_entries: List[UpcomingMealPlanEntry] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DashboardSummaryDto:
    stock_items: StockItemSummary
    shopping_lists: ShoppingListSummary
    products: ProductSummary
    recipes: RecipeSummary
    meals: MealSummary
    meal_plan: MealPlanSummary


class GetDashboardSummaryHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> DashboardSummaryDto:
        session = self.repository.session

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
        # "Items queued" = unticked lines. Reaching into the registry's
        # `metadata.tables` here was unreliable (the registry tracks a
        # separate MetaData from the one Flask-SQLAlchemy creates the
        # tables on, so the lookup intermittently raised KeyError).
        # Going through the entity query builder uses the same mapper
        # path as every other count() call in the codebase.
        from dora_api.domain.entities.shopping_list import ShoppingListLine
        is_ticked_field = EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED)
        shopping_list_items_count = self.repository.get(ShoppingListLine).count(
            is_ticked_field.eq(False)
        )

        # ── Products ──────────────────────────────────────────────────────
        total_products = self.repository.get(Product).count()

        # ── Recipes ───────────────────────────────────────────────────────
        total_recipes = self.repository.get(Recipe).count()
        favourite_recipes = self.repository.get(Recipe).count(
            EntityField(Recipe, Recipe.Fields.IS_FAVOURITE).eq(True)
        )
        # Cookable-now count via the shared cookability query (same rule the
        # recipe DTO + `?cookable` filter use — R-003). Excludes empty recipes.
        cookability = load_recipe_cookability(self.repository)
        cookable_recipes = sum(
            1 for missing, ingredient_count in cookability.values()
            if missing == 0 and ingredient_count > 0
        )

        # ── Meals ─────────────────────────────────────────────────────────
        # "Definitions" = recipes with any meals on hand. "In stock" =
        # the sum of available_meals across every recipe.
        total_meals_in_stock = session.execute(
            select(func.coalesce(func.sum(Recipe.available_meals), 0))
        ).scalar_one()
        total_meal_definitions = session.execute(
            select(func.count()).select_from(Recipe).where(Recipe.available_meals > 0)
        ).scalar_one()

        # ── Meal plan: upcoming entries within the next week ──────────────
        _Window = date.today() + timedelta(days=7)
        upcoming_entries_entities = (
            self.repository
            .get(MealPlanEntry)
            .include(MealPlanEntry.Fields.RECIPE)
            .all(
                EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR)
                .between(date.today(), _Window)
            )
        )
        upcoming_entries_entities.sort(key=lambda e: (e.scheduled_for, e.slot))
        upcoming_entries_dto: List[UpcomingMealPlanEntry] = [
            UpcomingMealPlanEntry(
                recipe_name = e.recipe.name,
                scheduled_for = e.scheduled_for,
                slot = e.slot,
                servings = e.servings,
            )
            for e in upcoming_entries_entities
        ]

        return DashboardSummaryDto(
            stock_items = StockItemSummary(
                total = total_stock_items,
                out_of_stock = out_of_stock_count,
                low_stock = low_stock_count,
            ),
            shopping_lists = ShoppingListSummary(
                total = total_lists,
                total_items = int(shopping_list_items_count),
            ),
            products = ProductSummary(total = total_products),
            recipes = RecipeSummary(
                total = total_recipes,
                favourites = favourite_recipes,
                cookable_count = cookable_recipes,
            ),
            meals = MealSummary(
                total_definitions = int(total_meal_definitions),
                total_in_stock = int(total_meals_in_stock),
            ),
            meal_plan = MealPlanSummary(
                upcoming_entries = upcoming_entries_dto,
            ),
        )

@DASHBOARD_ROUTER.route("/summary")
def get_dashboard_summary():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(GetDashboardSummaryHandler)
    _Summary = _Handler.handle()
    _Logger.debug(
        "Dashboard summary: %d stock items (%d low, %d out)",
        _Summary.stock_items.total,
        _Summary.stock_items.low_stock,
        _Summary.stock_items.out_of_stock,
    )
    return ok(_Summary)
