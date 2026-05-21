import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import MEAL_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  entity_existence_failures,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateMealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default = None, min_length = 1, max_length = 255)
    quantity_in_stock: int | None = Field(default = None, ge = 0)
    recipe_ids: List[UUID] | None = None


@dataclass(slots=True)
class UpdateMealResponse:
    meal_not_found: bool = False
    meal_already_exists: bool = False
    missing_recipe_ids: tuple[UUID, ...] = ()


class UpdateMealHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateMealRequest, meal_id: UUID) -> UpdateMealResponse:
        _Meal = (
            self.repository
            .get(Meal)
            .include(Meal.Fields.RECIPES)
            .one(EntityField(Meal, "id").eq(meal_id))
        )
        if not _Meal:
            return UpdateMealResponse(meal_not_found = True)

        _SetFields = request.model_fields_set

        if "name" in _SetFields and request.name is not None:
            _NameField = EntityField(Meal, Meal.Fields.NAME)
            _SameName: Meal | None = self.repository.get(Meal).one(_NameField.eq(request.name))
            if _SameName and _SameName.id != meal_id:
                return UpdateMealResponse(meal_already_exists = True)
            _Meal.name = request.name

        if "quantity_in_stock" in _SetFields and request.quantity_in_stock is not None:
            _Meal.quantity_in_stock = request.quantity_in_stock

        if "recipe_ids" in _SetFields and request.recipe_ids is not None:
            _NewRecipes: List[Recipe] = []
            _MissingIds: List[UUID] = []
            for _RecipeId in request.recipe_ids:
                _Recipe = self.repository.get(Recipe).by_id(_RecipeId)
                if not _Recipe:
                    _MissingIds.append(_RecipeId)
                    continue
                _NewRecipes.append(_Recipe)
            if _MissingIds:
                return UpdateMealResponse(missing_recipe_ids = tuple(_MissingIds))
            _Meal.recipes = _NewRecipes

        self.repository.save_changes()
        return UpdateMealResponse()


@MEAL_ROUTER.route("<meal_id>", methods=["PATCH"])
@has_request_body(UpdateMealRequest)
def update_meal(meal_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(UpdateMealHandler)
    _Request: UpdateMealRequest = get_request_body()
    _Response = _Handler.handle(_Request, meal_id)

    if _Response.meal_not_found:
        return not_found(Meal.__name__, meal_id)

    if _Response.meal_already_exists:
        return business_rule_violation(f"A meal with the name '{_Request.name}' already exists.")

    if _Response.missing_recipe_ids:
        _Logger.warning(f"Recipes not found: {_Response.missing_recipe_ids}")
        return entity_existence_failures(
            Recipe.__name__,
            field_of(UpdateMealRequest, 'recipe_ids'),
            *_Response.missing_recipe_ids,
        )

    return no_content()
