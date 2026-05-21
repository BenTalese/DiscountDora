import logging
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class DeleteRecipeResponse:
    recipe_not_found: bool = False


class DeleteRecipeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, recipe_id: UUID) -> DeleteRecipeResponse:
        _Recipe = (
            self.repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
            .one(EntityField(Recipe, "id").eq(recipe_id))
        )

        if not _Recipe:
            return DeleteRecipeResponse(recipe_not_found = True)

        self.repository.remove(_Recipe)
        self.repository.save_changes()

        return DeleteRecipeResponse()


@RECIPE_ROUTER.route("<recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to delete recipe.")
    _Handler: DeleteRecipeHandler = get_container().inject(DeleteRecipeHandler)
    _Response = _Handler.handle(recipe_id)

    if _Response.recipe_not_found:
        _Logger.warning(f"Recipe not found with ID: {recipe_id}")
        return not_found(Recipe.__name__, recipe_id)

    _Logger.info(f"Successfully deleted recipe with ID {recipe_id}.")
    return no_content()
