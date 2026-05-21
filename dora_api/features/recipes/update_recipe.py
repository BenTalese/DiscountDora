import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  entity_existence_failure,
                                                  entity_existence_failures,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateRecipeIngredientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock_item_id: UUID
    quantity: float | None = None
    unit: str | None = Field(default = None, max_length = 50)
    notes: str | None = Field(default = None, max_length = 255)


class UpdateRecipeRequest(BaseModel):
    """Partial update — only fields present in the request body are applied.

    Pydantic's `model_fields_set` is used to distinguish 'not provided' from
    'explicitly null'. Default values are placeholders and never applied.
    """
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default = None, min_length = 1, max_length = 255)
    category: str | None = None
    cook_time_minutes: int | None = None
    cuisine: str | None = None
    difficulty: str | None = None
    instructions: str | None = None
    is_favourite: bool | None = None
    nutrition: str | None = None
    prep_time_minutes: int | None = None
    recipe_collection_id: UUID | None = None
    servings: int | None = None
    time_of_day: str | None = None
    ingredients: List[UpdateRecipeIngredientRequest] | None = None


@dataclass(slots=True)
class UpdateRecipeResponse:
    recipe_not_found: bool = False
    recipe_already_exists: bool = False
    recipe_collection_not_found: bool = False
    missing_stock_item_ids: tuple[UUID, ...] = ()


# Attributes that may safely be assigned from the request as-is, including
# explicit nulls for the nullable ones. `is_favourite` is handled separately
# because the entity column is NOT NULL — accepting null from a PATCH would
# turn a request-level oversight into a 500 at commit time.
_NULLABLE_PLAIN_ATTRS = (
    "category", "cook_time_minutes", "cuisine", "difficulty",
    "instructions", "nutrition", "prep_time_minutes",
    "servings", "time_of_day",
)


class UpdateRecipeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateRecipeRequest, recipe_id: UUID) -> UpdateRecipeResponse:
        _Recipe: Recipe | None = (
            self.repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
            .one(EntityField(Recipe, "id").eq(recipe_id))
        )
        if not _Recipe:
            return UpdateRecipeResponse(recipe_not_found = True)

        _SetFields = request.model_fields_set

        if "name" in _SetFields and request.name is not None:
            _NameField = EntityField(Recipe, Recipe.Fields.NAME)
            _SameName: Recipe | None = self.repository.get(Recipe).one(_NameField.eq(request.name))
            if _SameName and _SameName.id != recipe_id:
                return UpdateRecipeResponse(recipe_already_exists = True)
            _Recipe.name = request.name

        if "recipe_collection_id" in _SetFields:
            if request.recipe_collection_id is None:
                _Recipe.recipe_collection = None
            else:
                _Collection = self.repository.get(RecipeCollection).by_id(request.recipe_collection_id)
                if not _Collection:
                    return UpdateRecipeResponse(recipe_collection_not_found = True)
                _Recipe.recipe_collection = _Collection

        if "ingredients" in _SetFields and request.ingredients is not None:
            _NewIngredients: List[RecipeIngredient] = []
            _MissingIds: List[UUID] = []
            for _IngredientRequest in request.ingredients:
                _StockItem = self.repository.get(StockItem).by_id(_IngredientRequest.stock_item_id)
                if not _StockItem:
                    _MissingIds.append(_IngredientRequest.stock_item_id)
                    continue
                _NewIngredients.append(RecipeIngredient(
                    notes = _IngredientRequest.notes,
                    quantity = _IngredientRequest.quantity,
                    stock_item = _StockItem,
                    unit = _IngredientRequest.unit,
                ))
            if _MissingIds:
                return UpdateRecipeResponse(missing_stock_item_ids = tuple(_MissingIds))
            for _Ingredient in _NewIngredients:
                self.repository.add(_Ingredient)
            _Recipe.ingredients = _NewIngredients

        for _Attr in _NULLABLE_PLAIN_ATTRS:
            if _Attr in _SetFields:
                setattr(_Recipe, _Attr, getattr(request, _Attr))

        # is_favourite is bool-non-nullable on the entity; ignore explicit nulls.
        if "is_favourite" in _SetFields and request.is_favourite is not None:
            _Recipe.is_favourite = request.is_favourite

        self.repository.save_changes()
        return UpdateRecipeResponse()


@RECIPE_ROUTER.route("<recipe_id>", methods=["PATCH"])
@has_request_body(UpdateRecipeRequest)
def update_recipe(recipe_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update recipe.")
    _Handler = get_container().inject(UpdateRecipeHandler)
    _Request: UpdateRecipeRequest = get_request_body()
    _Response = _Handler.handle(_Request, recipe_id)

    if _Response.recipe_not_found:
        _Logger.warning(f"Recipe not found with ID: {recipe_id}")
        return not_found(Recipe.__name__, recipe_id)

    if _Response.recipe_already_exists:
        _Logger.warning(f"Recipe already exists with name: {_Request.name}")
        return business_rule_violation(f"A recipe with the name '{_Request.name}' already exists.")

    if (_Response.recipe_collection_not_found
            and "recipe_collection_id" in _Request.model_fields_set
            and _Request.recipe_collection_id is not None):
        _Logger.warning(f"Recipe collection not found: {_Request.recipe_collection_id}")
        return entity_existence_failure(
            RecipeCollection.__name__,
            field_of(UpdateRecipeRequest, 'recipe_collection_id'),
            _Request.recipe_collection_id,
        )

    if _Response.missing_stock_item_ids:
        _Logger.warning(f"Stock items not found: {_Response.missing_stock_item_ids}")
        return entity_existence_failures(
            StockItem.__name__,
            field_of(UpdateRecipeRequest, 'ingredients'),
            *_Response.missing_stock_item_ids,
        )

    _Logger.info(f"Successfully updated recipe with ID: {recipe_id}")
    return no_content()
