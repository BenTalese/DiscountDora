import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


class AdjustRecipeMealsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Bounded for fat-finger protection — there's no undo on a pool
    # adjustment, and 999 covers any realistic batch-cook freezer haul.
    delta: int = Field(ge = -999, le = 999)


@dataclass(slots=True)
class AdjustRecipeMealsResponse:
    recipe_not_found: bool = False
    available_meals: int = 0


class AdjustRecipeMealsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: AdjustRecipeMealsRequest, recipe_id: UUID) -> AdjustRecipeMealsResponse:
        _Recipe = self.repository.get(Recipe).by_id(recipe_id)
        if not _Recipe:
            return AdjustRecipeMealsResponse(recipe_not_found = True)
        _New = (_Recipe.available_meals or 0) + request.delta
        # Floor at zero — adjustments can't push the pool negative; the
        # user is just telling us "I have this many" and a sub-zero
        # claim is meaningless.
        _Recipe.available_meals = max(_New, 0)
        self.repository.save_changes()
        return AdjustRecipeMealsResponse(available_meals = _Recipe.available_meals)


@RECIPE_ROUTER.route("<recipe_id>/adjust-meals", methods=["POST"])
@has_request_body(AdjustRecipeMealsRequest)
def adjust_recipe_meals(recipe_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = AdjustRecipeMealsHandler(SqlAlchemyRepository())
    _Request: AdjustRecipeMealsRequest = get_request_body()
    _Response = _Handler.handle(_Request, recipe_id)
    if _Response.recipe_not_found:
        return not_found(Recipe.__name__, recipe_id)
    _Logger.info(
        f"Adjusted recipe {recipe_id} meals by {_Request.delta} "
        f"(pool now {_Response.available_meals})"
    )
    return ok({"available_meals": _Response.available_meals})
