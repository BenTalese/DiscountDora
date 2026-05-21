import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.recipes.get_recipes import get_recipes
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created,
                                                  entity_existence_failure,
                                                  entity_existence_failures)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateRecipeIngredientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock_item_id: UUID
    quantity: float | None = None
    unit: str | None = Field(default = None, max_length = 50)
    notes: str | None = Field(default = None, max_length = 255)


class CreateRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length = 1, max_length = 255)
    category: str | None = Field(default = None, max_length = 255)
    cook_time_minutes: int | None = Field(default = None, ge = 0)
    cuisine: str | None = Field(default = None, max_length = 255)
    difficulty: str | None = Field(default = None, max_length = 50)
    instructions: str | None = None
    nutrition: str | None = None
    prep_time_minutes: int | None = Field(default = None, ge = 0)
    recipe_collection_id: UUID | None = None
    servings: int | None = Field(default = None, ge = 1)
    time_of_day: str | None = Field(default = None, max_length = 50)
    ingredients: List[CreateRecipeIngredientRequest] = Field(default_factory = list)


@dataclass(slots=True)
class CreateRecipeResponse:
    new_recipe_id: UUID = EMPTY_UUID
    recipe_already_exists: bool = False
    recipe_collection_not_found: bool = False
    missing_stock_item_ids: tuple[UUID, ...] = ()


class CreateRecipeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateRecipeRequest) -> CreateRecipeResponse:
        _RecipeName = EntityField(Recipe, Recipe.Fields.NAME)
        _ExistingRecipe: Recipe | None = (
            self.repository
            .get(Recipe)
            .one(_RecipeName.eq(request.name))
        )
        if _ExistingRecipe:
            return CreateRecipeResponse(recipe_already_exists = True)

        _Collection: RecipeCollection | None = None
        if request.recipe_collection_id:
            _Collection = self.repository.get(RecipeCollection).by_id(request.recipe_collection_id)
            if not _Collection:
                return CreateRecipeResponse(recipe_collection_not_found = True)

        _Ingredients: List[RecipeIngredient] = []
        _MissingIds: List[UUID] = []
        for _IngredientRequest in request.ingredients:
            _StockItem = self.repository.get(StockItem).by_id(_IngredientRequest.stock_item_id)
            if not _StockItem:
                _MissingIds.append(_IngredientRequest.stock_item_id)
                continue
            _Ingredients.append(RecipeIngredient(
                notes = _IngredientRequest.notes,
                quantity = _IngredientRequest.quantity,
                stock_item = _StockItem,
                unit = _IngredientRequest.unit,
            ))

        if _MissingIds:
            return CreateRecipeResponse(missing_stock_item_ids = tuple(_MissingIds))

        for _Ingredient in _Ingredients:
            self.repository.add(_Ingredient)

        _NewRecipe = Recipe(
            category = request.category,
            cook_time_minutes = request.cook_time_minutes,
            cuisine = request.cuisine,
            difficulty = request.difficulty,
            image = None,
            ingredients = _Ingredients,
            instructions = request.instructions,
            is_favourite = False,
            last_made_on = None,
            name = request.name,
            nutrition = request.nutrition,
            prep_time_minutes = request.prep_time_minutes,
            recipe_collection = _Collection,
            servings = request.servings,
            time_of_day = request.time_of_day,
        )

        self.repository.add(_NewRecipe)
        self.repository.save_changes()

        return CreateRecipeResponse(new_recipe_id = _NewRecipe.id)


@RECIPE_ROUTER.route("", methods=["POST"])
@has_request_body(CreateRecipeRequest)
def create_recipe():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to create recipe.")
    _Handler = get_container().inject(CreateRecipeHandler)
    _Request: CreateRecipeRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.recipe_already_exists:
        _Logger.warning(f"Recipe already exists with name: {_Request.name}")
        return business_rule_violation(f"A recipe with the name '{_Request.name}' already exists.")

    if _Response.recipe_collection_not_found and _Request.recipe_collection_id:
        _Logger.warning(f"Recipe collection not found: {_Request.recipe_collection_id}")
        return entity_existence_failure(
            RecipeCollection.__name__,
            field_of(CreateRecipeRequest, 'recipe_collection_id'),
            _Request.recipe_collection_id,
        )

    if _Response.missing_stock_item_ids:
        _Logger.warning(f"Stock items not found: {_Response.missing_stock_item_ids}")
        return entity_existence_failures(
            StockItem.__name__,
            field_of(CreateRecipeRequest, 'ingredients'),
            *_Response.missing_stock_item_ids,
        )

    _Logger.info(f"Successfully created recipe with ID: {_Response.new_recipe_id}")
    from dora_api.features.recipes.get_recipes import GetRecipesHandler
    _Dto = get_container().inject(GetRecipesHandler).handle_by_id(_Response.new_recipe_id)
    return created(
        _Response.new_recipe_id,
        f"{RECIPE_ROUTER.name}.{get_recipes.__name__}",
        "recipe_id",
        body = _Dto,
    )
