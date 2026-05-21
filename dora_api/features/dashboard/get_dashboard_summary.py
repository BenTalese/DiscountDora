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

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Stock level names used to bucket stock items. Kept here as a contract with
# the seeded values — if you ever rename a stock level via the UI/migration,
# this lookup falls back gracefully (count = 0) rather than 500.
OUT_OF_STOCK_NAME = "Out of Stock"
LOW_STOCK_NAME = "Low Stock"


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


@dataclass(frozen=True, slots=True)
class MealSummary:
    total_definitions: int
    total_in_stock: int


@dataclass(frozen=True, slots=True)
class UpcomingMealPlanEntry:
    meal_name: str
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
        total_stock_items = self.repository.get(StockItem).count()
        out_of_stock_id = self._stock_level_id_for(OUT_OF_STOCK_NAME)
        low_stock_id = self._stock_level_id_for(LOW_STOCK_NAME)

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
        is_archived_field = EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED)
        total_lists = self.repository.get(ShoppingList).count(is_archived_field.eq(False))
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

        # ── Meals ─────────────────────────────────────────────────────────
        total_meals = self.repository.get(Meal).count()
        # quantity_in_stock summed across all meal definitions.
        total_meals_in_stock = session.execute(
            select(func.coalesce(func.sum(Meal.quantity_in_stock), 0))
        ).scalar_one()

        # ── Meal plan: upcoming entries within the next week ──────────────
        # Window: today → today + 7 days. We pull entries with their meals
        # eager-loaded so the frontend can render names without a follow-up.
        _Window = date.today() + timedelta(days=7)
        upcoming_entries_entities = (
            self.repository
            .get(MealPlanEntry)
            .include(MealPlanEntry.Fields.MEAL)
            .all(
                EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR)
                .between(date.today(), _Window)
            )
        )
        upcoming_entries_entities.sort(key=lambda e: (e.scheduled_for, e.slot))
        upcoming_entries_dto: List[UpcomingMealPlanEntry] = [
            UpcomingMealPlanEntry(
                meal_name = e.meal.name,
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
            ),
            meals = MealSummary(
                total_definitions = total_meals,
                total_in_stock = int(total_meals_in_stock),
            ),
            meal_plan = MealPlanSummary(
                upcoming_entries = upcoming_entries_dto,
            ),
        )

    def _stock_level_id_for(self, name: str):
        level = self.repository.get(StockLevel).one(
            EntityField(StockLevel, StockLevel.Fields.NAME).eq(name)
        )
        return level.id if level else None


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
