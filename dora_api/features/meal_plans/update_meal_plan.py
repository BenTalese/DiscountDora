import logging
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe import Recipe
from dora_api.features.app_settings.clock import household_today
from dora_api.features.meal_slots.slot_validation import (
    find_invalid_slot, get_valid_slot_names, invalid_slot_message)
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  entity_existence_failures,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


class UpdateMealPlanEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: UUID
    scheduled_for: date
    servings: int = Field(default = 1, ge = 1)
    slot: str = Field(min_length = 1, max_length = 50)


class UpdateMealPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default = None, min_length = 1, max_length = 255)
    start_date: date | None = None
    entries: List[UpdateMealPlanEntryRequest] | None = None
    # Explicit opt-in for the destructive "clear every future entry"
    # path. Sending `entries: []` without this flag is rejected so a
    # caller can't accidentally nuke a plan by forgetting to populate
    # the array. Past/consumed entries are preserved regardless.
    confirm_clear_entries: bool = False


@dataclass(slots=True)
class UpdateMealPlanResponse:
    meal_plan_not_found: bool = False
    missing_recipe_ids: tuple[UUID, ...] = ()
    has_past_entry: bool = False
    needs_clear_confirmation: bool = False
    invalid_slot_message: str | None = None


class UpdateMealPlanHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: UpdateMealPlanRequest, meal_plan_id: UUID) -> UpdateMealPlanResponse:
        _Plan = (
            self.repository
            .get(MealPlan)
            .include(MealPlan.Fields.ENTRIES)
            .one(EntityField(MealPlan, "id").eq(meal_plan_id))
        )
        if not _Plan:
            return UpdateMealPlanResponse(meal_plan_not_found = True)

        _SetFields = request.model_fields_set

        if "name" in _SetFields and request.name is not None:
            _Plan.name = request.name
        if "start_date" in _SetFields and request.start_date is not None:
            _Plan.start_date = request.start_date

        if "entries" in _SetFields and request.entries is not None:
            if len(request.entries) == 0 and not request.confirm_clear_entries:
                return UpdateMealPlanResponse(needs_clear_confirmation = True)

            # validate slot names against the household MealSlot
            # vocabulary (R-010); off-vocab names rejected on new writes.
            _ValidSlots = get_valid_slot_names(self.repository)
            _BadSlot = find_invalid_slot(
                (_EntryRequest.slot for _EntryRequest in request.entries), _ValidSlots
            )
            if _BadSlot is not None:
                return UpdateMealPlanResponse(
                    invalid_slot_message = invalid_slot_message(_BadSlot, _ValidSlots)
                )

            _Today = household_today(self.repository)
            # Don't overwrite already-consumed entries (past days are
            # locked read-only); keep them as-is and replace only the
            # forward-looking portion of the plan.
            _ConsumedExisting = [
                _Entry for _Entry in (_Plan.entries or [])
                if _Entry.consumed_at is not None
            ]

            for _EntryRequest in request.entries:
                if _EntryRequest.scheduled_for < _Today:
                    return UpdateMealPlanResponse(has_past_entry = True)

            _NewEntries: List[MealPlanEntry] = []
            _MissingIds: List[UUID] = []
            for _EntryRequest in request.entries:
                _Recipe = self.repository.get(Recipe).by_id(_EntryRequest.recipe_id)
                if not _Recipe:
                    _MissingIds.append(_EntryRequest.recipe_id)
                    continue
                _NewEntries.append(MealPlanEntry(
                    recipe = _Recipe,
                    scheduled_for = _EntryRequest.scheduled_for,
                    servings = _EntryRequest.servings,
                    slot = _EntryRequest.slot,
                ))
            if _MissingIds:
                return UpdateMealPlanResponse(missing_recipe_ids = tuple(_MissingIds))
            for _Entry in _NewEntries:
                self.repository.add(_Entry)
            _Plan.entries = _ConsumedExisting + _NewEntries

        self.repository.save_changes()
        return UpdateMealPlanResponse()


@MEAL_PLAN_ROUTER.route("<uuid:meal_plan_id>", methods=["PATCH"])
@has_request_body(UpdateMealPlanRequest)
def update_meal_plan(meal_plan_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = UpdateMealPlanHandler(SqlAlchemyRepository())
    _Request: UpdateMealPlanRequest = get_request_body()
    _Response = _Handler.handle(_Request, meal_plan_id)

    if _Response.meal_plan_not_found:
        return not_found(MealPlan.__name__, meal_plan_id)

    if _Response.invalid_slot_message:
        return bad_request(_Response.invalid_slot_message)

    if _Response.has_past_entry:
        return bad_request("Meal plan entries cannot be scheduled in the past.")

    if _Response.needs_clear_confirmation:
        return bad_request(
            "Refusing to clear every future entry without confirmation. "
            "Resend with `confirm_clear_entries: true` if that's really the intent."
        )

    if _Response.missing_recipe_ids:
        _Logger.warning(f"Recipes not found: {_Response.missing_recipe_ids}")
        return entity_existence_failures(
            Recipe.__name__,
            field_of(UpdateMealPlanRequest, 'entries'),
            *_Response.missing_recipe_ids,
        )

    return no_content()
