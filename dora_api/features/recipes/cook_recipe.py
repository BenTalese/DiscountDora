import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CookRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Upper bound is paranoia, not policy — a fat-finger 99999 is
    # almost certainly a typo, and there's no undo on the pool.
    meals_cooked: int = Field(ge = 0, le = 999)


@dataclass(slots=True)
class CookRecipeResponse:
    recipe_not_found: bool = False
    available_meals: int = 0


class CookRecipeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CookRecipeRequest, recipe_id: UUID) -> CookRecipeResponse:
        _Recipe = self.repository.get(Recipe).by_id(recipe_id)
        if not _Recipe:
            return CookRecipeResponse(recipe_not_found = True)
        _Recipe.available_meals = (_Recipe.available_meals or 0) + request.meals_cooked
        _Recipe.last_made_on = datetime.now(UTC)
        self.repository.save_changes()
        return CookRecipeResponse(available_meals = _Recipe.available_meals)


@RECIPE_ROUTER.route("<recipe_id>/cook", methods=["POST"])
@has_request_body(CookRecipeRequest)
def cook_recipe(recipe_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(CookRecipeHandler)
    _Request: CookRecipeRequest = get_request_body()
    _Response = _Handler.handle(_Request, recipe_id)
    if _Response.recipe_not_found:
        return not_found(Recipe.__name__, recipe_id)
    _Logger.info(
        f"Cooked recipe {recipe_id}: +{_Request.meals_cooked} meals "
        f"(pool now {_Response.available_meals})"
    )
    if _Request.meals_cooked == 0:
        return no_content()
    return ok({"available_meals": _Response.available_meals})
