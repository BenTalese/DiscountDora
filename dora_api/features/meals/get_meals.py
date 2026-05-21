import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.meal import Meal
from dora_api.features.routers import MEAL_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class MealRecipeDto:
    recipe_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class MealDto:
    meal_id: UUID
    name: str
    quantity_in_stock: int
    recipes: List[MealRecipeDto]

    @classmethod
    def from_entity(cls, meal: Meal) -> 'MealDto':
        return MealDto(
            meal_id = meal.id,
            name = meal.name,
            quantity_in_stock = meal.quantity_in_stock,
            recipes = [MealRecipeDto(recipe_id = r.id, name = r.name) for r in (meal.recipes or [])],
        )


_FIELD_MAP: dict[str, EntityField] = {
    "meal_id": EntityField(Meal, "id"),
}


class GetMealsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def _base_query(self):
        return self.repository.get(Meal).include(Meal.Fields.RECIPES)

    def handle(self, options) -> Page[MealDto]:
        return self._base_query().paginate(
            options, MealDto.from_entity, field_map=_FIELD_MAP
        )

    def handle_by_id(self, meal_id: UUID) -> MealDto | None:
        entity = self._base_query().by_id(meal_id)
        return MealDto.from_entity(entity) if entity else None


@MEAL_ROUTER.route("")
def get_meals():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetMealsHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} meals.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
