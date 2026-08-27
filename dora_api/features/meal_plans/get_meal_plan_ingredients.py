import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class MealPlanIngredientDto:
    stock_item_id: UUID
    stock_item_name: str
    total_quantity: float | None
    unit: str | None
    used_in_recipe_ids: List[UUID]
    # Owner feedback 2026-08-27 — the shared add-to-list picker files optional
    # ingredients into their own unticked section, so the aggregate has to say
    # which items are optional. Aggregation means one stock item can arrive
    # from several ingredient rows across several recipes: it is optional only
    # when *every* contributing row was optional. One required row anywhere in
    # the week makes the item required (the same "required wins" rule the
    # recipe picker already applies within a single recipe — we would rather
    # over-stock than under-stock).
    is_optional: bool


@dataclass(frozen=True, slots=True)
class UnlinkedIngredientDto:
    """An ingredient row with no linked stock item, so it cannot become a
    shopping-list line. FU-505 surfaced these from the auto-generate endpoint;
    the picker-driven add (owner feedback 2026-08-27) replaced that call, so
    the aggregate has to carry them instead or the guarantee is silently
    lost."""
    recipe_name: str
    ingredient_name: str


@dataclass(frozen=True, slots=True)
class MealPlanIngredientsDto:
    """Envelope. Was a bare list until 2026-08-27; `unlinked` cannot be
    expressed per-item (those rows have no stock item to hang off)."""
    items: List[MealPlanIngredientDto]
    unlinked: List[UnlinkedIngredientDto]


def aggregate_meal_plan_ingredients(
    repository, recipe_id_to_servings: dict[UUID, int],
) -> MealPlanIngredientsDto:
    """Aggregate a {recipe_id: total_servings} demand into per-stock-item
    quantities, scaling each recipe's ingredient amounts by
    `servings / recipe.servings`. The single source of this scaling math (F34,
    R-003) — used by both the saved-plan ingredients endpoint and the
    sequential-builder preview."""
    if not recipe_id_to_servings:
        return MealPlanIngredientsDto(items=[], unlinked=[])

    aggregated: dict[UUID, dict] = {}
    unlinked: List[UnlinkedIngredientDto] = []
    for recipe_id, servings in recipe_id_to_servings.items():
        recipe = (
            repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
                .then_include(RecipeIngredient.Fields.STOCK_ITEM)
            .one(EntityField(Recipe, "id").eq(recipe_id))
        )
        if not recipe:
            continue
        recipe_servings = recipe.servings or 1
        scale = servings / recipe_servings if recipe_servings else 1
        for ingredient in recipe.ingredients or []:
            # An *unlinked* ingredient (paste-imported, never matched to a
            # pantry item — IMPL_PLAN_RECIPE_IMPORTER §Chunk 4) has no stock
            # item to aggregate against. This used to read `.id` off None and
            # 500 the whole endpoint, so both this preview and a saved plan's
            # ingredients died outright if any recipe in the selection had one
            # unlinked row. It still can't become a line — a shopping list is
            # a list of *stock items*, and "1 cup of something" isn't one — but
            # since 2026-08-27 it is *reported* rather than silently dropped,
            # so the add-to-list picker can name what it couldn't take.
            if ingredient.stock_item is None:
                unlinked.append(UnlinkedIngredientDto(
                    recipe_name = recipe.name,
                    ingredient_name = (ingredient.raw_text or "").strip()
                        or "(unnamed ingredient)",
                ))
                continue
            existing = aggregated.setdefault(ingredient.stock_item.id, {
                "stock_item_name": ingredient.stock_item.name,
                "total_quantity": 0.0 if ingredient.quantity is not None else None,
                "unit": ingredient.unit,
                "used_in_recipe_ids": set(),
                "is_optional": True,
            })
            if ingredient.quantity is not None and existing["total_quantity"] is not None:
                existing["total_quantity"] += ingredient.quantity * scale
            elif ingredient.quantity is not None:
                existing["total_quantity"] = ingredient.quantity * scale
            if existing["unit"] is None:
                existing["unit"] = ingredient.unit
            existing["used_in_recipe_ids"].add(recipe_id)
            # Required wins: one non-optional row anywhere clears the flag.
            if not ingredient.is_optional:
                existing["is_optional"] = False

    return MealPlanIngredientsDto(
        items = [
            MealPlanIngredientDto(
                stock_item_id = stock_item_id,
                stock_item_name = data["stock_item_name"],
                total_quantity = data["total_quantity"],
                unit = data["unit"],
                used_in_recipe_ids = list(data["used_in_recipe_ids"]),
                is_optional = data["is_optional"],
            )
            for stock_item_id, data in aggregated.items()
        ],
        unlinked = unlinked,
    )


class GetMealPlanIngredientsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, meal_plan_id: UUID) -> MealPlanIngredientsDto | None:
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

        return aggregate_meal_plan_ingredients(self.repository, _RecipeIdToServings)


@MEAL_PLAN_ROUTER.route("<uuid:meal_plan_id>/ingredients")
def get_meal_plan_ingredients(meal_plan_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = GetMealPlanIngredientsHandler(SqlAlchemyRepository())
    _Result = _Handler.handle(meal_plan_id)
    if _Result is None:
        return not_found(MealPlan.__name__, meal_plan_id)
    _Logger.info(
        f"Meal plan {meal_plan_id} has {len(_Result.items)} aggregated ingredients"
        f" ({len(_Result.unlinked)} unlinked)"
    )
    return ok(_Result)


# ───── Preview ingredients for an unsaved selection (C-2.J) ─────────────────

class PreviewRecipeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipe_id: UUID
    servings: int = Field(default=1, ge=1)


class PreviewIngredientsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipes: List[PreviewRecipeInput] = Field(default_factory=list)


class PreviewIngredientsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: PreviewIngredientsRequest) -> MealPlanIngredientsDto:
        recipe_id_to_servings: dict[UUID, int] = {}
        for r in request.recipes:
            recipe_id_to_servings[r.recipe_id] = recipe_id_to_servings.get(r.recipe_id, 0) + r.servings
        return aggregate_meal_plan_ingredients(self.repository, recipe_id_to_servings)


@MEAL_PLAN_ROUTER.route("preview-ingredients", methods=["POST"])
@has_request_body(PreviewIngredientsRequest)
def preview_meal_plan_ingredients():
    _Request: PreviewIngredientsRequest = get_request_body()
    _Result = PreviewIngredientsHandler(SqlAlchemyRepository()).handle(_Request)
    return ok(_Result)
