import logging
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.features.routers import RECIPE_COLLECTION_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class DeleteRecipeCollectionResponse:
    recipe_collection_not_found: bool = False


class DeleteRecipeCollectionHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, recipe_collection_id: UUID) -> DeleteRecipeCollectionResponse:
        _Collection = self.repository.get(RecipeCollection).by_id(recipe_collection_id)
        if not _Collection:
            return DeleteRecipeCollectionResponse(recipe_collection_not_found = True)

        # Recipes referencing this collection get recipe_collection_id NULLed by FK.
        self.repository.remove(_Collection)
        self.repository.save_changes()
        return DeleteRecipeCollectionResponse()


@RECIPE_COLLECTION_ROUTER.route("<recipe_collection_id>", methods=["DELETE"])
def delete_recipe_collection(recipe_collection_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(DeleteRecipeCollectionHandler)
    _Response = _Handler.handle(recipe_collection_id)

    if _Response.recipe_collection_not_found:
        return not_found(RecipeCollection.__name__, recipe_collection_id)

    _Logger.info(f"Deleted recipe collection {recipe_collection_id}")
    return no_content()
