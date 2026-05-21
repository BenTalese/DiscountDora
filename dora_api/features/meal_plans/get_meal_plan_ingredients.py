import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class MealPlanIngredientDto:
    stock_item_id: UUID
    stock_item_name: str
    total_quantity: float | None
    unit: str | None
    used_in_meal_ids: List[UUID]


class GetMealPlanIngredientsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, meal_plan_id: UUID) -> List[MealPlanIngredientDto] | None:
        _Plan = (
            self.repository
            .get(MealPlan)
            .include(MealPlan.Fields.ENTRIES)
                .then_include(MealPlanEntry.Fields.MEAL)
            .one(EntityField(MealPlan, "id").eq(meal_plan_id))
        )
        if not _Plan:
            return None

        # For each unique meal in the plan, load its recipes with ingredients.
        _MealIdToServings: dict[UUID, int] = {}
        for _Entry in _Plan.entries or []:
            _MealIdToServings[_Entry.meal.id] = _MealIdToServings.get(_Entry.meal.id, 0) + _Entry.servings

        if not _MealIdToServings:
            return []

        # Reload each meal with its recipes + ingredients + stock_item.
        # Two-step because the query builder doesn't chain 4 levels deep.
        _Aggregated: dict[UUID, dict] = {}

        for _MealId, _Servings in _MealIdToServings.items():
            _Meal = (
                self.repository
                .get(Meal)
                .include(Meal.Fields.RECIPES)
                .one(EntityField(Meal, "id").eq(_MealId))
            )
            if not _Meal:
                continue
            for _Recipe in _Meal.recipes or []:
                _LoadedRecipe = (
                    self.repository
                    .get(Recipe)
                    .include(Recipe.Fields.INGREDIENTS)
                        .then_include(RecipeIngredient.Fields.STOCK_ITEM)
                    .one(EntityField(Recipe, "id").eq(_Recipe.id))
                )
                if not _LoadedRecipe:
                    continue
                _RecipeServings = _LoadedRecipe.servings or 1
                _Scale = _Servings / _RecipeServings if _RecipeServings else 1
                for _Ingredient in _LoadedRecipe.ingredients or []:
                    _Existing = _Aggregated.setdefault(_Ingredient.stock_item.id, {
                        "stock_item_name": _Ingredient.stock_item.name,
                        "total_quantity": 0.0 if _Ingredient.quantity is not None else None,
                        "unit": _Ingredient.unit,
                        "used_in_meal_ids": set(),
                    })
                    if _Ingredient.quantity is not None and _Existing["total_quantity"] is not None:
                        _Existing["total_quantity"] += _Ingredient.quantity * _Scale
                    elif _Ingredient.quantity is not None:
                        # Previously was None, take this as the running total
                        _Existing["total_quantity"] = _Ingredient.quantity * _Scale
                    if _Existing["unit"] is None:
                        _Existing["unit"] = _Ingredient.unit
                    _Existing["used_in_meal_ids"].add(_MealId)

        return [
            MealPlanIngredientDto(
                stock_item_id = _StockItemId,
                stock_item_name = _Data["stock_item_name"],
                total_quantity = _Data["total_quantity"],
                unit = _Data["unit"],
                used_in_meal_ids = list(_Data["used_in_meal_ids"]),
            )
            for _StockItemId, _Data in _Aggregated.items()
        ]


@MEAL_PLAN_ROUTER.route("<meal_plan_id>/ingredients")
def get_meal_plan_ingredients(meal_plan_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(GetMealPlanIngredientsHandler)
    _Result = _Handler.handle(meal_plan_id)
    if _Result is None:
        return not_found(MealPlan.__name__, meal_plan_id)
    _Logger.info(f"Meal plan {meal_plan_id} has {len(_Result)} aggregated ingredients")
    return ok(_Result)
