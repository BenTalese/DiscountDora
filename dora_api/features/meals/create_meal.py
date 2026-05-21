import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.meals.get_meals import get_meals
from dora_api.features.routers import MEAL_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created,
                                                  entity_existence_failures)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateMealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length = 1, max_length = 255)
    quantity_in_stock: int = Field(default = 0, ge = 0)
    recipe_ids: List[UUID] = Field(default_factory = list)


@dataclass(slots=True)
class CreateMealResponse:
    new_meal_id: UUID = EMPTY_UUID
    meal_already_exists: bool = False
    missing_recipe_ids: tuple[UUID, ...] = ()


class CreateMealHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateMealRequest) -> CreateMealResponse:
        _NameField = EntityField(Meal, Meal.Fields.NAME)
        if self.repository.get(Meal).one(_NameField.eq(request.name)):
            return CreateMealResponse(meal_already_exists = True)

        _Recipes: List[Recipe] = []
        _MissingIds: List[UUID] = []
        for _RecipeId in request.recipe_ids:
            _Recipe = self.repository.get(Recipe).by_id(_RecipeId)
            if not _Recipe:
                _MissingIds.append(_RecipeId)
                continue
            _Recipes.append(_Recipe)

        if _MissingIds:
            return CreateMealResponse(missing_recipe_ids = tuple(_MissingIds))

        _NewMeal = Meal(
            name = request.name,
            quantity_in_stock = request.quantity_in_stock,
            recipes = _Recipes,
        )
        self.repository.add(_NewMeal)
        self.repository.save_changes()
        return CreateMealResponse(new_meal_id = _NewMeal.id)


@MEAL_ROUTER.route("", methods=["POST"])
@has_request_body(CreateMealRequest)
def create_meal():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(CreateMealHandler)
    _Request: CreateMealRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.meal_already_exists:
        return business_rule_violation(f"A meal with the name '{_Request.name}' already exists.")

    if _Response.missing_recipe_ids:
        _Logger.warning(f"Recipes not found: {_Response.missing_recipe_ids}")
        return entity_existence_failures(
            Recipe.__name__,
            field_of(CreateMealRequest, 'recipe_ids'),
            *_Response.missing_recipe_ids,
        )

    from dora_api.features.meals.get_meals import GetMealsHandler
    _Dto = get_container().inject(GetMealsHandler).handle_by_id(_Response.new_meal_id)
    return created(
        _Response.new_meal_id,
        f"{MEAL_ROUTER.name}.{get_meals.__name__}",
        "meal_id",
        body = _Dto,
    )
