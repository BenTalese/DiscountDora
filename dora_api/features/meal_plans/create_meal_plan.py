import logging
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.cook_batch import CookBatch
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.app_settings.clock import household_today
from dora_api.features.meal_plans.cook_batch_grouping import (
    group_by_cook_key, validate_cook_groups)
from dora_api.features.meal_plans.get_meal_plans import get_meal_plans
from dora_api.features.meal_slots.slot_validation import (
    find_invalid_slot, get_valid_slot_names, invalid_slot_message)
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import (bad_request, created,
                                                  entity_existence_failures)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_request_body)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


class CreateMealPlanEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: UUID
    scheduled_for: date
    servings: int = Field(default = 1, ge = 1)
    slot: str = Field(min_length = 1, max_length = 50)
    # PROPOSAL_MEAL_PLANS_PART_2 — optional transient grouping token. Entries
    # sharing a `cook_key` become one CookBatch (cook once, eat several days).
    # It is NOT a DB id — the server materialises a fresh CookBatch per group.
    cook_key: str | None = Field(default = None, max_length = 64)
    # Owner 2026-09-04 — cooked on the day, outside the cooked-portion pool.
    # Mutually exclusive with `cook_key` (validated in `validate_cook_groups`).
    cook_fresh: bool = False


class CreateMealPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Optional (C-2.E): the planner creates nameless week-plans. A name may
    # still be supplied (e.g. templates / legacy callers).
    name: str | None = Field(default = None, max_length = 255)
    start_date: date
    entries: List[CreateMealPlanEntryRequest] = Field(default_factory = list)


@dataclass(slots=True)
class CreateMealPlanResponse:
    new_meal_plan_id: UUID = EMPTY_UUID
    missing_recipe_ids: tuple[UUID, ...] = ()
    has_past_entry: bool = False
    invalid_slot_message: str | None = None
    invalid_cook_batch_message: str | None = None


class CreateMealPlanHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: CreateMealPlanRequest) -> CreateMealPlanResponse:
        _Today = household_today(self.repository)

        # validate slot names against the household MealSlot
        # vocabulary at the boundary (R-010). Slots are free-text labels,
        # not FKs; off-vocab names are rejected on new writes.
        _ValidSlots = get_valid_slot_names(self.repository)
        _BadSlot = find_invalid_slot(
            (_EntryRequest.slot for _EntryRequest in request.entries), _ValidSlots
        )
        if _BadSlot is not None:
            return CreateMealPlanResponse(
                invalid_slot_message = invalid_slot_message(_BadSlot, _ValidSlots)
            )

        # PROPOSAL_MEAL_PLANS_PART_2 — structural validation of any cook-batch
        # groups (same recipe + slot, distinct days, >=2 entries) before any write.
        _CookBatchError = validate_cook_groups(request.entries)
        if _CookBatchError is not None:
            return CreateMealPlanResponse(invalid_cook_batch_message = _CookBatchError)

        for _EntryRequest in request.entries:
            if _EntryRequest.scheduled_for < _Today:
                return CreateMealPlanResponse(has_past_entry = True)

        # Resolve recipes once (a cook group repeats a recipe id) before any write,
        # so a missing recipe never leaves an orphan plan/batch behind.
        _RecipeById: dict[UUID, Recipe] = {}
        _MissingIds: List[UUID] = []
        for _EntryRequest in request.entries:
            if _EntryRequest.recipe_id in _RecipeById:
                continue
            _Recipe = self.repository.get(Recipe).by_id(_EntryRequest.recipe_id)
            if not _Recipe:
                _MissingIds.append(_EntryRequest.recipe_id)
            else:
                _RecipeById[_EntryRequest.recipe_id] = _Recipe
        if _MissingIds:
            return CreateMealPlanResponse(missing_recipe_ids = tuple(_MissingIds))

        # Plan first (batches FK it), then batches (entries FK them), then entries.
        # No relationships link plan<-batch or entry->batch, so flush between each
        # so SQLite's FK check sees the parent row (repository.flush contract).
        _NewPlan = MealPlan(name = request.name, start_date = request.start_date, entries = [])
        self.repository.add(_NewPlan)
        self.repository.flush()

        _BatchByKey: dict[str, CookBatch] = {}
        for _Key, _Members in group_by_cook_key(request.entries).items():
            _Batch = CookBatch(meal_plan_id = _NewPlan.id, recipe_id = _Members[0].recipe_id)
            self.repository.add(_Batch)
            _BatchByKey[_Key] = _Batch
        if _BatchByKey:
            self.repository.flush()

        _Entries: List[MealPlanEntry] = []
        for _EntryRequest in request.entries:
            _Batch = _BatchByKey.get(_EntryRequest.cook_key) if _EntryRequest.cook_key else None
            _Entry = MealPlanEntry(
                recipe = _RecipeById[_EntryRequest.recipe_id],
                scheduled_for = _EntryRequest.scheduled_for,
                servings = _EntryRequest.servings,
                slot = _EntryRequest.slot,
                cook_batch_id = _Batch.id if _Batch else None,
                cook_fresh = _EntryRequest.cook_fresh,
            )
            self.repository.add(_Entry)
            _Entries.append(_Entry)
        _NewPlan.entries = _Entries

        self.repository.save_changes()
        return CreateMealPlanResponse(new_meal_plan_id = _NewPlan.id)


@MEAL_PLAN_ROUTER.route("", methods=["POST"])
@has_request_body(CreateMealPlanRequest)
def create_meal_plan():
    _Logger = logging.getLogger(__name__)
    _Handler = CreateMealPlanHandler(SqlAlchemyRepository())
    _Request: CreateMealPlanRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.invalid_slot_message:
        return bad_request(_Response.invalid_slot_message)

    if _Response.invalid_cook_batch_message:
        return bad_request(_Response.invalid_cook_batch_message)

    if _Response.has_past_entry:
        return bad_request("Meal plan entries cannot be scheduled in the past.")

    if _Response.missing_recipe_ids:
        _Logger.warning(f"Recipes not found: {_Response.missing_recipe_ids}")
        return entity_existence_failures(
            Recipe.__name__,
            field_of(CreateMealPlanRequest, 'entries'),
            *_Response.missing_recipe_ids,
        )

    from dora_api.features.meal_plans.get_meal_plans import GetMealPlansHandler
    _Dto = GetMealPlansHandler(SqlAlchemyRepository()).handle_by_id(
        _Response.new_meal_plan_id
    )
    return created(
        _Response.new_meal_plan_id,
        f"{MEAL_PLAN_ROUTER.name}.{get_meal_plans.__name__}",
        "meal_plan_id",
        body = _Dto,
    )
