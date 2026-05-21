import logging
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import (entity_existence_failures,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateMealPlanEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meal_id: UUID
    scheduled_for: date
    servings: int = Field(default = 1, ge = 1)
    slot: str = Field(min_length = 1, max_length = 50)


class UpdateMealPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default = None, min_length = 1, max_length = 255)
    start_date: date | None = None
    entries: List[UpdateMealPlanEntryRequest] | None = None


@dataclass(slots=True)
class UpdateMealPlanResponse:
    meal_plan_not_found: bool = False
    missing_meal_ids: tuple[UUID, ...] = ()


class UpdateMealPlanHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

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
            _NewEntries: List[MealPlanEntry] = []
            _MissingIds: List[UUID] = []
            for _EntryRequest in request.entries:
                _Meal = self.repository.get(Meal).by_id(_EntryRequest.meal_id)
                if not _Meal:
                    _MissingIds.append(_EntryRequest.meal_id)
                    continue
                _NewEntries.append(MealPlanEntry(
                    meal = _Meal,
                    scheduled_for = _EntryRequest.scheduled_for,
                    servings = _EntryRequest.servings,
                    slot = _EntryRequest.slot,
                ))
            if _MissingIds:
                return UpdateMealPlanResponse(missing_meal_ids = tuple(_MissingIds))
            for _Entry in _NewEntries:
                self.repository.add(_Entry)
            _Plan.entries = _NewEntries

        self.repository.save_changes()
        return UpdateMealPlanResponse()


@MEAL_PLAN_ROUTER.route("<meal_plan_id>", methods=["PATCH"])
@has_request_body(UpdateMealPlanRequest)
def update_meal_plan(meal_plan_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(UpdateMealPlanHandler)
    _Request: UpdateMealPlanRequest = get_request_body()
    _Response = _Handler.handle(_Request, meal_plan_id)

    if _Response.meal_plan_not_found:
        return not_found(MealPlan.__name__, meal_plan_id)

    if _Response.missing_meal_ids:
        _Logger.warning(f"Meals not found: {_Response.missing_meal_ids}")
        return entity_existence_failures(
            Meal.__name__,
            field_of(UpdateMealPlanRequest, 'entries'),
            *_Response.missing_meal_ids,
        )

    return no_content()
