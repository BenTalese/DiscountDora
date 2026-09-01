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
from dora_api.features.app_settings.clock import household_today
from dora_api.features.meal_plans.cook_batch_grouping import (
    group_by_cook_key, validate_cook_groups)
from dora_api.features.meal_slots.slot_validation import (
    allowed_slot_names, find_invalid_slot, get_valid_slot_names,
    invalid_slot_message)
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
    # PROPOSAL_MEAL_PLANS_PART_2 — transient grouping token; entries sharing a
    # `cook_key` become one CookBatch. Not a DB id (see create_meal_plan).
    cook_key: str | None = Field(default = None, max_length = 64)


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
    invalid_cook_batch_message: str | None = None


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

            # Validate slot names against the household MealSlot vocabulary
            # (R-010) PLUS the labels this plan already carries. Deleting a
            # slot is deliberately non-cascading — existing entries keep their
            # label — and the planner resends every forward entry on each edit,
            # so validating the payload against the live vocabulary alone made
            # the whole week unsaveable the moment one entry held a deleted
            # slot (owner report 2026-09-01). A genuinely NEW off-vocab slot is
            # still refused; see `allowed_slot_names`.
            _ValidSlots = get_valid_slot_names(self.repository)
            _AllowedSlots = allowed_slot_names(
                _ValidSlots, (_Entry.slot for _Entry in (_Plan.entries or []))
            )
            _BadSlot = find_invalid_slot(
                (_EntryRequest.slot for _EntryRequest in request.entries), _AllowedSlots
            )
            if _BadSlot is not None:
                # The message names the current vocabulary, not the allowance:
                # "Allowed: …, Snack" would read as an invitation to keep using
                # a slot the household has deleted.
                return UpdateMealPlanResponse(
                    invalid_slot_message = invalid_slot_message(_BadSlot, _ValidSlots)
                )

            # PROPOSAL_MEAL_PLANS_PART_2 — validate cook-batch groups before any write.
            _CookBatchError = validate_cook_groups(request.entries)
            if _CookBatchError is not None:
                return UpdateMealPlanResponse(invalid_cook_batch_message = _CookBatchError)

            _Today = household_today(self.repository)
            # Preserve the immutable past. Past days are read-only, so the
            # client resends only forward-looking entries; anything already
            # in the plan that is consumed OR scheduled before today is
            # history we keep as-is, replacing only the forward portion.
            # FU-595: this must cover past-*unconsumed* entries too, not just
            # consumed ones. A past day the user didn't cook (auto-drain off,
            # or "Didn't cook") is unconsumed; if it weren't preserved here the
            # replace would silently drop it, and the old client's workaround
            # of resending it tripped the past-date guard below — freezing the
            # whole week. Preserve it server-side; the client no longer sends it.
            _PreservedExisting = [
                _Entry for _Entry in (_Plan.entries or [])
                if _Entry.consumed_at is not None or _Entry.scheduled_for < _Today
            ]

            # A forward entry scheduled before today is a genuine
            # "can't schedule in the past" error — the client never sends past
            # entries any more, so this guards against real bad input, not the
            # FU-595 resend case (which no longer reaches here).
            for _EntryRequest in request.entries:
                if _EntryRequest.scheduled_for < _Today:
                    return UpdateMealPlanResponse(has_past_entry = True)

            # Resolve recipes once (a cook group repeats a recipe id) before any
            # write, so a missing recipe never leaves an orphan batch behind.
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
                return UpdateMealPlanResponse(missing_recipe_ids = tuple(_MissingIds))

            # PROPOSAL_MEAL_PLANS_PART_2 — the forward portion is replaced, so its
            # CookBatches are too. Keep only batches still referenced by a preserved
            # (past/consumed) entry; delete the rest of this plan's batches. Their
            # forward entries are about to be delete-orphaned; the SET NULL FK means
            # deleting a batch first can't trip an FK error.
            _PreservedBatchIds = {
                _Entry.cook_batch_id for _Entry in _PreservedExisting
                if _Entry.cook_batch_id is not None
            }
            _ExistingBatches = self.repository.get(CookBatch).all(
                EntityField(CookBatch, CookBatch.Fields.MEAL_PLAN_ID).eq(meal_plan_id)
            )
            for _Batch in _ExistingBatches:
                if _Batch.id not in _PreservedBatchIds:
                    self.repository.remove(_Batch)
            self.repository.flush()

            # Rebuild the forward batches from the resent cook_keys.
            _BatchByKey: dict[str, CookBatch] = {}
            for _Key, _Members in group_by_cook_key(request.entries).items():
                _Batch = CookBatch(meal_plan_id = meal_plan_id, recipe_id = _Members[0].recipe_id)
                self.repository.add(_Batch)
                _BatchByKey[_Key] = _Batch
            if _BatchByKey:
                self.repository.flush()

            _NewEntries: List[MealPlanEntry] = []
            for _EntryRequest in request.entries:
                _Batch = _BatchByKey.get(_EntryRequest.cook_key) if _EntryRequest.cook_key else None
                _NewEntries.append(MealPlanEntry(
                    recipe = _RecipeById[_EntryRequest.recipe_id],
                    scheduled_for = _EntryRequest.scheduled_for,
                    servings = _EntryRequest.servings,
                    slot = _EntryRequest.slot,
                    cook_batch_id = _Batch.id if _Batch else None,
                ))
            for _Entry in _NewEntries:
                self.repository.add(_Entry)
            _Plan.entries = _PreservedExisting + _NewEntries

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

    if _Response.invalid_cook_batch_message:
        return bad_request(_Response.invalid_cook_batch_message)

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
