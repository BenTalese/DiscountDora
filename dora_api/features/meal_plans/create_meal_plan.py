import logging
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal import Meal
from dora_api.domain.entities.meal_plan import MealPlan
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.meal_plans.get_meal_plans import get_meal_plans
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import (created,
                                                  entity_existence_failures)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateMealPlanEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meal_id: UUID
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
    missing_meal_ids: tuple[UUID, ...] = ()


class CreateMealPlanHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateMealPlanRequest) -> CreateMealPlanResponse:
        _Entries: List[MealPlanEntry] = []
        _MissingIds: List[UUID] = []
        for _EntryRequest in request.entries:
            _Meal = self.repository.get(Meal).by_id(_EntryRequest.meal_id)
            if not _Meal:
                _MissingIds.append(_EntryRequest.meal_id)
                continue
            _Entries.append(MealPlanEntry(
                meal = _Meal,
                scheduled_for = _EntryRequest.scheduled_for,
                servings = _EntryRequest.servings,
                slot = _EntryRequest.slot,
            ))

        if _MissingIds:
            return CreateMealPlanResponse(missing_meal_ids = tuple(_MissingIds))

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

    if _Response.missing_meal_ids:
        _Logger.warning(f"Meals not found: {_Response.missing_meal_ids}")
        return entity_existence_failures(
            Meal.__name__,
            field_of(CreateMealPlanRequest, 'entries'),
            *_Response.missing_meal_ids,
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
