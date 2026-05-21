import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.meal import Meal
from dora_api.features.routers import MEAL_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class AdjustMealStockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delta: int


@dataclass(slots=True)
class AdjustMealStockResponse:
    meal_not_found: bool = False
    would_go_negative: bool = False


class AdjustMealStockHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: AdjustMealStockRequest, meal_id: UUID) -> AdjustMealStockResponse:
        _Meal = self.repository.get(Meal).by_id(meal_id)
        if not _Meal:
            return AdjustMealStockResponse(meal_not_found = True)
        _New = _Meal.quantity_in_stock + request.delta
        if _New < 0:
            return AdjustMealStockResponse(would_go_negative = True)
        _Meal.quantity_in_stock = _New
        self.repository.save_changes()
        return AdjustMealStockResponse()


@MEAL_ROUTER.route("<meal_id>/adjust-stock", methods=["POST"])
@has_request_body(AdjustMealStockRequest)
def adjust_meal_stock(meal_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(AdjustMealStockHandler)
    _Request: AdjustMealStockRequest = get_request_body()
    _Response = _Handler.handle(_Request, meal_id)
    if _Response.meal_not_found:
        return not_found(Meal.__name__, meal_id)
    if _Response.would_go_negative:
        return business_rule_violation("Meal stock cannot go below zero.")
    _Logger.info(f"Adjusted meal {meal_id} stock by {_Request.delta}")
    return no_content()
