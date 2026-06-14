import logging
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.meal_plans.get_meal_plans import get_meal_plans
from dora_api.features.meal_slots.slot_validation import (
    find_invalid_slot, get_valid_slot_names, invalid_slot_message)
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import (bad_request, created,
                                                  entity_existence_failures)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateMealPlanEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: UUID
    scheduled_for: date
    servings: int = Field(default = 1, ge = 1)
    slot: str = Field(min_length = 1, max_length = 50)


class CreateMealPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length = 1, max_length = 255)
    start_date: date
    entries: List[CreateMealPlanEntryRequest] = Field(default_factory = list)


@dataclass(slots=True)
class CreateMealPlanResponse:
    new_meal_plan_id: UUID = EMPTY_UUID
    missing_recipe_ids: tuple[UUID, ...] = ()
    has_past_entry: bool = False
    invalid_slot_message: str | None = None


class CreateMealPlanHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateMealPlanRequest) -> CreateMealPlanResponse:
        _Today = date.today()

        # C-2.A — validate slot names against the household MealSlot
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

        for _EntryRequest in request.entries:
            if _EntryRequest.scheduled_for < _Today:
                return CreateMealPlanResponse(has_past_entry = True)

        _Entries: List[MealPlanEntry] = []
        _MissingIds: List[UUID] = []
        for _EntryRequest in request.entries:
            _Recipe = self.repository.get(Recipe).by_id(_EntryRequest.recipe_id)
            if not _Recipe:
                _MissingIds.append(_EntryRequest.recipe_id)
                continue
            _Entries.append(MealPlanEntry(
                recipe = _Recipe,
                scheduled_for = _EntryRequest.scheduled_for,
                servings = _EntryRequest.servings,
                slot = _EntryRequest.slot,
            ))

        if _MissingIds:
            return CreateMealPlanResponse(missing_recipe_ids = tuple(_MissingIds))

        for _Entry in _Entries:
            self.repository.add(_Entry)

        _NewPlan = MealPlan(
            name = request.name,
            start_date = request.start_date,
            entries = _Entries,
        )
        self.repository.add(_NewPlan)
        self.repository.save_changes()
        return CreateMealPlanResponse(new_meal_plan_id = _NewPlan.id)


@MEAL_PLAN_ROUTER.route("", methods=["POST"])
@has_request_body(CreateMealPlanRequest)
def create_meal_plan():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(CreateMealPlanHandler)
    _Request: CreateMealPlanRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.invalid_slot_message:
        return bad_request(_Response.invalid_slot_message)

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
    _Dto = get_container().inject(GetMealPlansHandler).handle_by_id(
        _Response.new_meal_plan_id
    )
    return created(
        _Response.new_meal_plan_id,
        f"{MEAL_PLAN_ROUTER.name}.{get_meal_plans.__name__}",
        "meal_plan_id",
        body = _Dto,
    )
