import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from dora_api.domain.entities.meal_plan import MealPlan
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
    used_in_recipe_ids: List[UUID]


class GetMealPlanIngredientsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, meal_plan_id: UUID) -> List[MealPlanIngredientDto] | None:
        _Plan = (
            self.repository
            .get(MealPlan)
            .include(MealPlan.Fields.ENTRIES)
            .one(EntityField(MealPlan, "id").eq(meal_plan_id))
        )
        if not _Plan:
            return None

        _RecipeIdToServings: dict[UUID, int] = {}
        for _Entry in _Plan.entries or []:
            if _Entry.consumed_at is not None:
                # Past entries already reduced the pool — they don't
                # contribute to the forward-looking shopping list.
                continue
            _RecipeIdToServings[_Entry._recipe_id] = (
                _RecipeIdToServings.get(_Entry._recipe_id, 0) + _Entry.servings
            )

        if not _RecipeIdToServings:
            return []

        _Aggregated: dict[UUID, dict] = {}

        for _RecipeId, _Servings in _RecipeIdToServings.items():
            _Recipe = (
                self.repository
                .get(Recipe)
                .include(Recipe.Fields.INGREDIENTS)
                    .then_include(RecipeIngredient.Fields.STOCK_ITEM)
                .one(EntityField(Recipe, "id").eq(_RecipeId))
            )
            if not _Recipe:
                continue
            _RecipeServings = _Recipe.servings or 1
            _Scale = _Servings / _RecipeServings if _RecipeServings else 1
            for _Ingredient in _Recipe.ingredients or []:
                _Existing = _Aggregated.setdefault(_Ingredient.stock_item.id, {
                    "stock_item_name": _Ingredient.stock_item.name,
                    "total_quantity": 0.0 if _Ingredient.quantity is not None else None,
                    "unit": _Ingredient.unit,
                    "used_in_recipe_ids": set(),
                })
                if _Ingredient.quantity is not None and _Existing["total_quantity"] is not None:
                    _Existing["total_quantity"] += _Ingredient.quantity * _Scale
                elif _Ingredient.quantity is not None:
                    _Existing["total_quantity"] = _Ingredient.quantity * _Scale
                if _Existing["unit"] is None:
                    _Existing["unit"] = _Ingredient.unit
                _Existing["used_in_recipe_ids"].add(_RecipeId)

        return [
            MealPlanIngredientDto(
                stock_item_id = _StockItemId,
                stock_item_name = _Data["stock_item_name"],
                total_quantity = _Data["total_quantity"],
                unit = _Data["unit"],
                used_in_recipe_ids = list(_Data["used_in_recipe_ids"]),
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
