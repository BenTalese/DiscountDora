import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class MealPlanEntryDto:
    meal_plan_entry_id: UUID
    recipe_id: UUID
    recipe_name: str
    scheduled_for: date
    servings: int
    slot: str
    consumed_at: datetime | None

    @classmethod
    def from_entity(cls, entry: MealPlanEntry) -> 'MealPlanEntryDto':
        return MealPlanEntryDto(
            meal_plan_entry_id = entry.id,
            recipe_id = entry.recipe.id,
            recipe_name = entry.recipe.name,
            scheduled_for = entry.scheduled_for,
            servings = entry.servings,
            slot = entry.slot,
            consumed_at = entry.consumed_at,
        )


@dataclass(frozen=True, slots=True)
class MealPlanDto:
    meal_plan_id: UUID
    name: str
    start_date: date
    entries: List[MealPlanEntryDto]

    @classmethod
    def from_entity(cls, plan: MealPlan) -> 'MealPlanDto':
        return MealPlanDto(
            meal_plan_id = plan.id,
            name = plan.name,
            start_date = plan.start_date,
            entries = [MealPlanEntryDto.from_entity(e) for e in (plan.entries or [])],
        )


_FIELD_MAP: dict[str, EntityField] = {
    "meal_plan_id": EntityField(MealPlan, "id"),
}


class GetMealPlansHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def _base_query(self):
        return (
            self.repository
            .get(MealPlan)
            .include(MealPlan.Fields.ENTRIES)
                .then_include(MealPlanEntry.Fields.RECIPE)
        )

    def handle(self, options) -> Page[MealPlanDto]:
        return self._base_query().paginate(
            options, MealPlanDto.from_entity, field_map=_FIELD_MAP
        )

    def handle_by_id(self, meal_plan_id: UUID) -> MealPlanDto | None:
        entity = self._base_query().by_id(meal_plan_id)
        return MealPlanDto.from_entity(entity) if entity else None


@MEAL_PLAN_ROUTER.route("")
def get_meal_plans():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetMealPlansHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} meal plans.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
