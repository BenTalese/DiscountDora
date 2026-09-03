"""The upcoming plan, and which of it the cooked-batch pool already covers.

One authority (R-003) for a question three surfaces were about to ask
separately: *of the meals still on the plan, which ones does somebody still
have to cook?*

The model is a **pool and a queue**. `Recipe.available_meals` is the pool —
portions already cooked and sitting in the fridge or freezer. The queue is
every un-consumed meal-plan entry from today forward, in date order. Walking
the queue and spending the pool tells you, per entry, whether it is already
covered or still needs cooking; totalling that per recipe is the shortfall
report the meal planner has always shown.

Both readings were previously computed independently — `get_shortfall.py`
compared `SUM(servings)` against `available_meals` in raw SQL, which answers
the recipe-level question and cannot answer the per-entry one. Owner,
2026-09-03, asked for the per-entry reading in order to say *"you've got 3
planned fried rice in the coming weeks and 2 have been allocated a meal, and
they need rice, and you're low on rice"* — the "2 have been allocated" clause
is exactly this allocation. Rather than write it a second time beside the
first, the pool model lives here and `get_shortfall` reads it.

**Coverage is all-or-nothing per entry, and deliberately conservative.** An
entry for 4 servings against a pool of 3 counts as *not* covered, not as 75%
covered: you are going to cook that meal, so its ingredients are demand. The
leftover 3 stay in the pool for a later, smaller entry — which is what a
household actually does with a half-batch.

A **cook batch** (one cook, several days) is a single allocation unit, not one
per day — see `allocate_pool`. Its leftover days are covered by their own
cook, so they never read as needing one.

A **fresh meal** (`MealPlanEntry.cook_fresh`) is outside the model entirely: it
is cooked on its day, so the pool neither pays for it nor is paid by it. It
never reads as covered, and `recipe_shortfalls` leaves it out of the committed
total — asking a batch household to cook two extra portions of Saturday's
roast, because Saturday's roast is on the plan, is the opposite of what the
mark means.

The queue is ordered by date, so the pool is spent on the *soonest* meals.
That is both what happens in a real kitchen and the reading that makes the
"earliest needed" date honest: if anything is uncovered, the earliest
uncovered date is the day the ingredients have to exist by.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from uuid import UUID

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.features.app_settings.clock import household_today
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class PlannedMeal:
    """One un-consumed, upcoming meal-plan entry, with its coverage verdict."""
    entry_id: UUID
    recipe_id: UUID
    recipe_name: str
    scheduled_for: date
    servings: int
    # True when the recipe's already-cooked pool stretches to this entry.
    covered: bool
    # PROPOSAL_MEAL_PLANS_PART_2 — the cook batch this entry belongs to, if
    # any. A batch is ONE cook eaten across several days, so the pool is spent
    # against the batch as a whole rather than per day (see `allocate_pool`).
    cook_batch_id: UUID | None = None
    # True when this entry is the day the cook actually happens (the batch's
    # earliest day), or when the meal is standalone. A leftover day is never
    # something anybody has to cook.
    is_cook_day: bool = True
    # Owner 2026-09-04 — this meal is cooked on the day, outside the pool. It
    # is never `covered` (no portion is spent on it) and it never contributes
    # to a recipe's shortfall (it asks the pool for nothing). See
    # `MealPlanEntry.cook_fresh`.
    cook_fresh: bool = False


@dataclass(frozen=True, slots=True)
class PlannedMealSnapshot:
    """Everything the pool model produced in one read.

    `available_by_recipe` rides along because every consumer that wants the
    per-entry coverage also wants the recipe-level totals, and re-reading
    `Recipe.available_meals` to get them would be a second query for a number
    we already had in hand.
    """
    meals: list[PlannedMeal]
    available_by_recipe: dict[UUID, int]


@dataclass(frozen=True, slots=True)
class RecipeShortfall:
    recipe_id: UUID
    recipe_name: str
    available_meals: int
    committed_meals: int
    shortfall: int
    earliest_needed: date | None


def allocate_pool(meals: list[PlannedMeal], available_meals: int) -> list[PlannedMeal]:
    """Spend `available_meals` across one recipe's entries, soonest first.

    Pure — no repo access — so the rule is unit-testable on its own. Returns
    the same entries with `covered` and `is_cook_day` decided, in date order.

    **A cook batch is one unit, not several.** Its days share a single cook, so
    the pool is spent against the batch's whole yield on its earliest day; the
    later days eat that cook's output and are never something anybody has to
    cook, whatever the pool holds. Allocating per day instead would let a pool
    of 2 "cover" the Monday of a Mon+Wed batch and leave the Wednesday reading
    as a second cook that does not exist (owner, 2026-09-03: *"changing cook
    days ... feels like a feature that has great potential to break"*).
    """
    remaining = max(0, available_meals)

    # Group into allocation units: one per standalone meal, one per batch.
    units: dict[str, list[PlannedMeal]] = {}
    for meal in meals:
        key = f"batch:{meal.cook_batch_id}" if meal.cook_batch_id else f"entry:{meal.entry_id}"
        units.setdefault(key, []).append(meal)

    def unit_sort_key(rows: list[PlannedMeal]):
        first = min(rows, key=lambda m: (m.scheduled_for, str(m.entry_id)))
        return (first.scheduled_for, str(first.entry_id))

    out: list[PlannedMeal] = []
    for rows in sorted(units.values(), key=unit_sort_key):
        # A fresh meal is cooked on its own day and never touches the pool, so
        # no portion is spent on it and it can never read as covered (owner
        # 2026-09-04). `cook_fresh` is mutually exclusive with a cook batch, so
        # this is always a one-entry unit.
        if any(m.cook_fresh for m in rows):
            out.extend(replace(meal, covered=False, is_cook_day=True) for meal in rows)
            continue
        cook_day = min(rows, key=lambda m: (m.scheduled_for, str(m.entry_id)))
        yield_needed = sum(m.servings for m in rows)
        covered = yield_needed <= remaining
        if covered:
            remaining -= yield_needed
        for meal in rows:
            is_cook_day = meal.entry_id == cook_day.entry_id
            out.append(replace(
                meal,
                # A leftover day is covered by its own batch's cook, so it is
                # never flagged as needing one.
                covered=covered or not is_cook_day,
                is_cook_day=is_cook_day,
            ))
    out.sort(key=lambda m: (m.scheduled_for, str(m.entry_id)))
    return out


def upcoming_planned_meals(
    repository: SqlAlchemyRepository,
    *,
    today: date | None = None,
    horizon_days: int | None = None,
) -> PlannedMealSnapshot:
    """Every un-consumed plan entry from `today` forward, coverage resolved.

    `horizon_days` bounds how far ahead to look. None means "the whole plan",
    which is the right default for the shortfall report — a meal you have
    committed to is committed whether it is three days or three weeks away.
    """
    if today is None:
        today = household_today(repository)

    query = (
        repository.get(MealPlanEntry)
        .where(EntityField(MealPlanEntry, MealPlanEntry.Fields.CONSUMED_AT).is_null())
        .where(EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).gte(today))
    )
    if horizon_days is not None:
        query = query.where(
            EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR)
            .lte(today + timedelta(days=horizon_days))
        )
    entries: list[MealPlanEntry] = query.all()
    if not entries:
        return PlannedMealSnapshot(meals=[], available_by_recipe={})

    # R-032: `MealPlanEntry.recipe` is `lazy="noload"`, so reading it off these
    # instances returns None *silently* even with an `.include()` — the exact
    # shape that made the buy-verdict endpoint answer "unsure" for every item
    # (see `_level_access.py`). Read the FK off the private mapped column and
    # fetch the recipes by id in one query instead.
    recipe_ids = {e._recipe_id for e in entries if e._recipe_id is not None}
    recipes_by_id: dict[UUID, Recipe] = {}
    if recipe_ids:
        recipes_by_id = {
            r.id: r for r in repository.get(Recipe).all(
                EntityField(Recipe, "id").in_(list(recipe_ids))
            )
        }

    by_recipe: dict[UUID, list[PlannedMeal]] = {}
    available_by_recipe: dict[UUID, int] = {}
    for entry in entries:
        recipe = recipes_by_id.get(entry._recipe_id) if entry._recipe_id else None
        if recipe is None:
            # A plan entry with no recipe cannot imply ingredient demand, and
            # it has no pool to spend. Skip rather than guess.
            continue
        by_recipe.setdefault(recipe.id, []).append(PlannedMeal(
            entry_id=entry.id,
            recipe_id=recipe.id,
            recipe_name=recipe.name,
            scheduled_for=entry.scheduled_for,
            servings=int(entry.servings or 0),
            covered=False,
            cook_batch_id=entry.cook_batch_id,
            cook_fresh=bool(getattr(entry, "cook_fresh", False)),
        ))
        available_by_recipe[recipe.id] = int(recipe.available_meals or 0)

    meals: list[PlannedMeal] = []
    for recipe_id, rows in by_recipe.items():
        meals.extend(allocate_pool(rows, available_by_recipe.get(recipe_id, 0)))
    return PlannedMealSnapshot(meals=meals, available_by_recipe=available_by_recipe)


def recipe_shortfalls(snapshot: PlannedMealSnapshot) -> list[RecipeShortfall]:
    """Roll the snapshot up per recipe into the shortfall report's shape.

    Pure, for the same reason `allocate_pool` is. `shortfall` stays defined as
    *committed servings beyond the pool* — the number the planner has always
    shown — rather than "count of uncovered entries", which is a different
    (and, for a report about how much to cook, less useful) number.

    Fresh meals are skipped outright (owner 2026-09-04): they neither draw on
    the pool nor need one stocked for them, so counting them as committed would
    inflate every figure this report produces.
    """
    grouped: dict[UUID, list[PlannedMeal]] = {}
    for meal in snapshot.meals:
        if meal.cook_fresh:
            continue
        grouped.setdefault(meal.recipe_id, []).append(meal)

    out: list[RecipeShortfall] = []
    for recipe_id, rows in grouped.items():
        committed = sum(m.servings for m in rows)
        available = snapshot.available_by_recipe.get(recipe_id, 0)
        if committed <= available:
            continue
        uncovered = [m for m in rows if not m.covered and m.is_cook_day]
        out.append(RecipeShortfall(
            recipe_id=recipe_id,
            recipe_name=rows[0].recipe_name,
            available_meals=available,
            committed_meals=committed,
            shortfall=committed - available,
            earliest_needed=min((m.scheduled_for for m in uncovered), default=None),
        ))
    out.sort(key=lambda r: (r.earliest_needed or date.max, r.recipe_name.lower()))
    return out
