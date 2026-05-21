import logging
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.meal import Meal
from dora_api.features.routers import MEAL_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class DeleteMealResponse:
    meal_not_found: bool = False


class DeleteMealHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, meal_id: UUID) -> DeleteMealResponse:
        _Meal = self.repository.get(Meal).by_id(meal_id)
        if not _Meal:
            return DeleteMealResponse(meal_not_found = True)
        self.repository.remove(_Meal)
        self.repository.save_changes()
        return DeleteMealResponse()


@MEAL_ROUTER.route("<meal_id>", methods=["DELETE"])
def delete_meal(meal_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(DeleteMealHandler)
    _Response = _Handler.handle(meal_id)
    if _Response.meal_not_found:
        return not_found(Meal.__name__, meal_id)
    _Logger.info(f"Deleted meal {meal_id}")
    return no_content()
