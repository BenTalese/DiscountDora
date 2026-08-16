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
    # PROPOSAL_MEAL_PLANS_PART_2 — cook-batch view fields. `cook_batch_id` groups
    # the linked meals; the rest are DERIVED server-side across the batch's entries
    # (state-ownership) and set in MealPlanDto.from_entity, not here:
    #   is_cook_day             — this entry is the batch's earliest day (the cook)
    #   cook_batch_total_servings — Σ servings across the batch (the yield to cook)
    #   cook_batch_size         — number of linked days
    # All null/false for a standalone meal (cook_batch_id is None).
    cook_batch_id: UUID | None = None
    is_cook_day: bool = False
    cook_batch_total_servings: int | None = None
    cook_batch_size: int | None = None
    # FU-637 — what one serving of this meal costs, calorie-wise, for the
    # install's current nutrition mode. Server-owned via
    # `effective_kcal_per_serving` so the planner, the cookbook card and the
    # kcal filter can't disagree about the same recipe (R-003). NULL when
    # nutrition is off, or when the recipe has no figure.
    kcal_per_serving: float | None = None
    kcal_is_reliable: bool = False

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
            cook_batch_id = entry.cook_batch_id,
        )


@dataclass(frozen=True, slots=True)
class MealPlanDayNutritionDto:
    """FU-637 — one day's planned calories, per serving.

    The figure answers "if I eat one serving of each meal planned for this
    day, what's that?" — which is the question a calorie-conscious cook is
    actually asking while building a week, and the only one Dora can answer
    honestly: a meal plan schedules *pots of food*, not plates for named
    people (`MealPlanEntry` has no eater), so per-person intake is not a
    number this app has, and won't invent.

    Coverage travels with it (R-041): `counted_meals` of `total_meals`.
    A meal whose figure isn't reliable is left out of the sum and shows up in
    the shortfall rather than quietly dragging the total down.
    """
    scheduled_for: date
    kcal_per_serving: float | None
    counted_meals: int
    total_meals: int


@dataclass(frozen=True, slots=True)
class MealPlanDto:
    meal_plan_id: UUID
    name: str | None
    start_date: date
    entries: List[MealPlanEntryDto]
    # FU-637 — per-day rollup over `entries`, server-side because summing a
    # fetched collection is exactly the cross-entity aggregate the
    # state-ownership rule keeps out of the client.
    day_nutrition: List['MealPlanDayNutritionDto'] = dataclasses.field(default_factory=list)

    @classmethod
    def from_entity(cls, plan: MealPlan) -> 'MealPlanDto':
        entries = [MealPlanEntryDto.from_entity(e) for e in (plan.entries or [])]
        return MealPlanDto(
            meal_plan_id = plan.id,
            name = plan.name,
            start_date = plan.start_date,
            entries = _apply_cook_batch_view(entries),
        )


def _apply_cook_batch_view(entries: List['MealPlanEntryDto']) -> List['MealPlanEntryDto']:
    """PROPOSAL_MEAL_PLANS_PART_2 — fill each linked entry's derived cook-batch
    view (is_cook_day / total yield / size) from the group as a whole. The cook
    happens on the batch's earliest day; total yield is what that one cook must
    produce. Standalone entries (no cook_batch_id) pass through untouched.
    """
    from collections import defaultdict
    members: dict = defaultdict(list)
    for entry in entries:
        if entry.cook_batch_id is not None:
            members[entry.cook_batch_id].append(entry)
    if not members:
        return entries

    aggregate: dict = {}
    for batch_id, group in members.items():
        aggregate[batch_id] = {
            "cook_day": min(e.scheduled_for for e in group),
            "total": sum(e.servings for e in group),
            "size": len(group),
        }
    return [
        entry if entry.cook_batch_id is None else dataclasses.replace(
            entry,
            is_cook_day = entry.scheduled_for == aggregate[entry.cook_batch_id]["cook_day"],
            cook_batch_total_servings = aggregate[entry.cook_batch_id]["total"],
            cook_batch_size = aggregate[entry.cook_batch_id]["size"],
        )
        for entry in entries
    ]


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

    def _hydrate_nutrition(self, plans: list[MealPlanDto]) -> list[MealPlanDto]:
        """FU-637 — per-entry and per-day calories across every plan in the page.

        Costs a constant number of queries: one to load the distinct recipes
        with their ingredients (the plan query deliberately doesn't carry
        ingredients — nothing else on this endpoint needs them), then the
        rollup's own three. Skipped entirely when nutrition is off, so the
        endpoint pays nothing for a feature the install isn't using.
        """
        from collections import defaultdict

        from dora_api.domain.entities.app_setting import (
            NUTRITION_MODE_COMPLEX, NUTRITION_MODE_OFF,
        )
        from dora_api.domain.entities.recipe import Recipe
        from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
        from dora_api.features.app_settings.access import get_or_create_app_setting
        from dora_api.features.nutrition.recipe_rollup import (
            effective_kcal_per_serving, input_from_entity, rollup_recipes_nutrition,
        )
        from dora_api.features.nutrition.sources import nutrition_mode

        mode = nutrition_mode(get_or_create_app_setting(self.repository))
        if mode == NUTRITION_MODE_OFF or not plans:
            return plans

        recipe_ids = list({
            entry.recipe_id for plan in plans for entry in plan.entries
        })
        if not recipe_ids:
            return plans

        recipes = (
            self.repository.get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
                .then_include(RecipeIngredient.Fields.STOCK_ITEM)
            .all(EntityField(Recipe, "id").in_(recipe_ids))
        )
        rollups = (
            rollup_recipes_nutrition(
                self.repository, [input_from_entity(r) for r in recipes]
            )
            if mode == NUTRITION_MODE_COMPLEX else {}
        )
        figure_by_recipe = {
            recipe.id: effective_kcal_per_serving(
                mode, recipe.kcal, rollups.get(recipe.id),
            )
            for recipe in recipes
        }

        def _day_rows(entries: list[MealPlanEntryDto]) -> list[MealPlanDayNutritionDto]:
            by_day: dict = defaultdict(list)
            for entry in entries:
                by_day[entry.scheduled_for].append(entry)
            rows = []
            for day, day_entries in sorted(by_day.items()):
                counted = [e for e in day_entries if e.kcal_is_reliable and e.kcal_per_serving]
                rows.append(MealPlanDayNutritionDto(
                    scheduled_for = day,
                    # None rather than 0.0 when nothing counted — zero would
                    # read as "a day of no calories" (R-041).
                    kcal_per_serving = (
                        round(sum(e.kcal_per_serving for e in counted)) if counted else None
                    ),
                    counted_meals = len(counted),
                    total_meals = len(day_entries),
                ))
            return rows

        hydrated = []
        for plan in plans:
            entries = [
                dataclasses.replace(
                    entry,
                    **dict(zip(
                        ("kcal_per_serving", "kcal_is_reliable"),
                        figure_by_recipe.get(entry.recipe_id, (None, False)),
                    )),
                )
                for entry in plan.entries
            ]
            hydrated.append(dataclasses.replace(
                plan, entries=entries, day_nutrition=_day_rows(entries),
            ))
        return hydrated

    def handle(self, options) -> Page[MealPlanDto]:
        page = self._base_query().paginate(
            options, MealPlanDto.from_entity, field_map=_FIELD_MAP
        )
        hydrated = self._hydrate_nutrition(
            self._hydrate_entry_has_image(list(page.items))
        )
        return Page(items=hydrated, total=page.total, page=page.page, limit=page.limit)

    def handle_by_id(self, meal_plan_id: UUID) -> MealPlanDto | None:
        entity = self._base_query().by_id(meal_plan_id)
        if not entity:
            return None
        dto = MealPlanDto.from_entity(entity)
        return self._hydrate_nutrition(self._hydrate_entry_has_image([dto]))[0]


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
