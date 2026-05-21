import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class MarkRecipeMadeResponse:
    recipe_not_found: bool = False


class MarkRecipeMadeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, recipe_id: UUID) -> MarkRecipeMadeResponse:
        _Recipe = self.repository.get(Recipe).by_id(recipe_id)
        if not _Recipe:
            return MarkRecipeMadeResponse(recipe_not_found = True)

        _Recipe.last_made_on = datetime.now(UTC)
        self.repository.save_changes()
        return MarkRecipeMadeResponse()


@RECIPE_ROUTER.route("<recipe_id>/mark-made", methods=["POST"])
def mark_recipe_made(recipe_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info(f"Marking recipe as made: {recipe_id}")
    _Handler = get_container().inject(MarkRecipeMadeHandler)
    _Response = _Handler.handle(recipe_id)

    if _Response.recipe_not_found:
        return not_found(Recipe.__name__, recipe_id)

    return no_content()
