import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class RecipeIngredientDto:
    recipe_ingredient_id: UUID
    stock_item_id: UUID
    stock_item_name: str
    stock_level_id: UUID | None
    # Direct location only — the frontend resolves the full breadcrumb via
    # the cached locations tree so recipe queries stay cheap.
    stock_location_id: UUID | None
    stock_location_name: str | None
    quantity: float | None
    unit: str | None
    notes: str | None

    @classmethod
    def from_entity(cls, ingredient: RecipeIngredient) -> 'RecipeIngredientDto':
        _Item = ingredient.stock_item
        _Loc = _Item.stock_location if _Item else None
        return RecipeIngredientDto(
            recipe_ingredient_id = ingredient.id,
            stock_item_id = _Item.id,
            stock_item_name = _Item.name,
            stock_level_id = _Item.stock_level.id if _Item.stock_level else None,
            stock_location_id = _Loc.id if _Loc else None,
            stock_location_name = _Loc.name if _Loc else None,
            quantity = ingredient.quantity,
            unit = ingredient.unit,
            notes = ingredient.notes,
        )


@dataclass(frozen=True, slots=True)
class RecipeDto:
    recipe_id: UUID
    name: str
    category: str | None
    cook_time_minutes: int | None
    cuisine: str | None
    difficulty: str | None
    instructions: str | None
    is_favourite: bool
    last_made_on: datetime | None
    nutrition: str | None
    prep_time_minutes: int | None
    recipe_collection_id: UUID | None
    servings: int | None
    time_of_day: str | None
    ingredients: List[RecipeIngredientDto]

    @classmethod
    def from_entity(cls, recipe: Recipe) -> 'RecipeDto':
        return RecipeDto(
            recipe_id = recipe.id,
            name = recipe.name,
            category = recipe.category,
            cook_time_minutes = recipe.cook_time_minutes,
            cuisine = recipe.cuisine,
            difficulty = recipe.difficulty,
            instructions = recipe.instructions,
            is_favourite = recipe.is_favourite,
            last_made_on = recipe.last_made_on,
            nutrition = recipe.nutrition,
            prep_time_minutes = recipe.prep_time_minutes,
            recipe_collection_id = recipe.recipe_collection.id if recipe.recipe_collection else None,
            servings = recipe.servings,
            time_of_day = recipe.time_of_day,
            ingredients = [RecipeIngredientDto.from_entity(i) for i in (recipe.ingredients or [])],
        )


_FIELD_MAP: dict[str, EntityField] = {
    "recipe_id": EntityField(Recipe, "id"),
    "recipe_collection_id": EntityField(Recipe, "_recipe_collection_id"),
}


class GetRecipesHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def _base_query(self):
        return (
            self.repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
                .then_include(RecipeIngredient.Fields.STOCK_ITEM)
                .then_include(StockItem.Fields.STOCK_LEVEL)
            .include(Recipe.Fields.INGREDIENTS)
                .then_include(RecipeIngredient.Fields.STOCK_ITEM)
                .then_include(StockItem.Fields.STOCK_LOCATION)
            .include(Recipe.Fields.RECIPE_COLLECTION)
        )

    def handle(self, options) -> Page[RecipeDto]:
        return self._base_query().paginate(
            options, RecipeDto.from_entity, field_map=_FIELD_MAP
        )

    def handle_by_id(self, recipe_id: UUID) -> RecipeDto | None:
        entity = self._base_query().by_id(recipe_id)
        return RecipeDto.from_entity(entity) if entity else None


@RECIPE_ROUTER.route("")
def get_recipes():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    try:
        _Page = get_container().inject(GetRecipesHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} recipes.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
