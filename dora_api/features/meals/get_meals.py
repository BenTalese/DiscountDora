import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.meal import Meal
from dora_api.features.recipes.recipe_tag_access import get_tags_for_recipes
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
    # P2-08 — tags derived by intersecting the tags of every constituent
    # recipe. A meal is honestly "vegan" only if *every* recipe in it is
    # tagged vegan, so we use set intersection rather than union — the
    # opposite would surface false-positive dietary claims. Read-only;
    # set automatically by the handler after the base query.
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_entity(cls, meal: Meal, tags: list[str] | None = None) -> 'MealDto':
        return MealDto(
            meal_id = meal.id,
            name = meal.name,
            quantity_in_stock = meal.quantity_in_stock,
            recipes = [MealRecipeDto(recipe_id = r.id, name = r.name) for r in (meal.recipes or [])],
            tags = tags or [],
        )


_FIELD_MAP: dict[str, EntityField] = {
    "meal_id": EntityField(Meal, "id"),
}


def _intersect_tags(recipe_ids: list[UUID]) -> list[str]:
    """A meal's effective tag set is the intersection of its recipes' tags.
    Empty input or any tagless recipe → empty intersection (honest "we
    can't claim this meal is vegan/gluten-free/etc.")."""
    if not recipe_ids:
        return []
    tag_map = get_tags_for_recipes(recipe_ids)
    sets: list[set[str]] = []
    for rid in recipe_ids:
        sets.append(set(tag_map.get(rid, [])))
    if not sets or any(len(s) == 0 for s in sets):
        # A single untagged recipe blanks the intersection — better to
        # show no tags than to imply a claim we can't substantiate.
        return []
    common = set.intersection(*sets) if sets else set()
    return sorted(common)


class GetMealsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def _base_query(self):
        return self.repository.get(Meal).include(Meal.Fields.RECIPES)

    def _hydrate_tags(self, dtos: list[MealDto]) -> list[MealDto]:
        if not dtos:
            return dtos
        return [
            dataclasses.replace(
                d, tags=_intersect_tags([r.recipe_id for r in d.recipes]),
            )
            for d in dtos
        ]

    def handle(self, options) -> Page[MealDto]:
        page = self._base_query().paginate(
            options, MealDto.from_entity, field_map=_FIELD_MAP
        )
        page.items = self._hydrate_tags(page.items)
        return page

    def handle_by_id(self, meal_id: UUID) -> MealDto | None:
        entity = self._base_query().by_id(meal_id)
        if entity is None:
            return None
        dto = MealDto.from_entity(entity)
        return dataclasses.replace(
            dto,
            tags=_intersect_tags([r.recipe_id for r in dto.recipes]),
        )


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
