import dataclasses
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import List
from uuid import UUID

from flask import request
from sqlalchemy import bindparam, text

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class MealPlanEntryDto:
    meal_plan_entry_id: UUID
    recipe_id: UUID
    recipe_name: str
    scheduled_for: date
    servings: int
    slot: str
    consumed_at: datetime | None
    # IMPL_PLAN_MEAL_PLANS_REBUILD §6.5 / Q6 — display fields for the
    # content-forward "rich" meal card used by Direction B. Pulled from the
    # already-loaded `entry.recipe` (cook_time_minutes / category / cuisine
    # come for free from the existing then_include + selectin loads).
    # `has_image` is bulk-hydrated via a single SQL pass so the deferred
    # `image` bytes column is never loaded just to set a boolean — same
    # pattern get_recipes._hydrate_has_image uses (FU-090).
    cook_time_minutes: int | None
    category_name: str | None
    cuisine_name: str | None
    has_image: bool = False

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
            cook_time_minutes = entry.recipe.cook_time_minutes,
            category_name = entry.recipe.category.name if entry.recipe.category else None,
            cuisine_name = entry.recipe.cuisine.name if entry.recipe.cuisine else None,
        )


@dataclass(frozen=True, slots=True)
class MealPlanDto:
    meal_plan_id: UUID
    name: str | None
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
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def _base_query(self):
        # Recipe.cuisine / Recipe.category are noload now; the
        # MealPlanEntryDto reads both, so chain sibling then_includes off
        # the entry.recipe path. Re-`include(ENTRIES)` resets the chain
        # so each `then_include` starts fresh (see get_recipes._base_query
        # for the same idiom on Recipe.INGREDIENTS).
        from dora_api.domain.entities.recipe import Recipe
        return (
            self.repository
            .get(MealPlan)
            .include(MealPlan.Fields.ENTRIES)
                .then_include(MealPlanEntry.Fields.RECIPE)
            .include(MealPlan.Fields.ENTRIES)
                .then_include(MealPlanEntry.Fields.RECIPE)
                .then_include(Recipe.Fields.CUISINE)
            .include(MealPlan.Fields.ENTRIES)
                .then_include(MealPlanEntry.Fields.RECIPE)
                .then_include(Recipe.Fields.CATEGORY)
        )

    def _hydrate_entry_has_image(self, plans: list[MealPlanDto]) -> list[MealPlanDto]:
        """Bulk-derive `has_image` for every entry across every plan in one
        SQL pass. Mirrors get_recipes._hydrate_has_image (FU-090) so the
        deferred `image` bytes column is never loaded just to set a flag.
        """
        recipe_ids: set[str] = set()
        for plan in plans:
            for entry in plan.entries:
                recipe_ids.add(str(entry.recipe_id))
        if not recipe_ids:
            return plans

        from dora_api.app import db
        from sqlalchemy import select
        from dora_api.domain.entities.recipe import Recipe as _Recipe
        # ORM select() — raw text() with str-UUID bindings silently returns
        # zero rows on SQLite's BINARY(16) id column (bug class fixed with
        # get_recipes._hydrate_has_image).
        stmt = select(_Recipe.id, _Recipe.image.is_not(None)).where(
            _Recipe.id.in_([UUID(r) for r in recipe_ids])
        )
        rows = db.session.execute(stmt).all()
        flag_by_id = {str(row[0]): bool(row[1]) for row in rows}

        return [
            dataclasses.replace(
                plan,
                entries=[
                    dataclasses.replace(
                        entry,
                        has_image=flag_by_id.get(str(entry.recipe_id), False),
                    )
                    for entry in plan.entries
                ],
            )
            for plan in plans
        ]

    def handle(self, options) -> Page[MealPlanDto]:
        page = self._base_query().paginate(
            options, MealPlanDto.from_entity, field_map=_FIELD_MAP
        )
        hydrated = self._hydrate_entry_has_image(list(page.items))
        return Page(items=hydrated, total=page.total, page=page.page, limit=page.limit)

    def handle_by_id(self, meal_plan_id: UUID) -> MealPlanDto | None:
        entity = self._base_query().by_id(meal_plan_id)
        if not entity:
            return None
        dto = MealPlanDto.from_entity(entity)
        return self._hydrate_entry_has_image([dto])[0]


@MEAL_PLAN_ROUTER.route("")
def get_meal_plans():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = GetMealPlansHandler(SqlAlchemyRepository()).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} meal plans.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
