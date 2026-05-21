import logging
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.recipe_collections.get_recipe_collections import \
    get_recipe_collections
from dora_api.features.routers import RECIPE_COLLECTION_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateRecipeCollectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length = 1, max_length = 255)


@dataclass(slots=True)
class CreateRecipeCollectionResponse:
    new_recipe_collection_id: UUID = EMPTY_UUID
    recipe_collection_already_exists: bool = False


class CreateRecipeCollectionHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateRecipeCollectionRequest) -> CreateRecipeCollectionResponse:
        _NameField = EntityField(RecipeCollection, RecipeCollection.Fields.NAME)
        _Existing: RecipeCollection | None = self.repository.get(RecipeCollection).one(_NameField.eq(request.name))
        if _Existing:
            return CreateRecipeCollectionResponse(recipe_collection_already_exists = True)

        _New = RecipeCollection(name = request.name)
        self.repository.add(_New)
        self.repository.save_changes()
        return CreateRecipeCollectionResponse(new_recipe_collection_id = _New.id)


@RECIPE_COLLECTION_ROUTER.route("", methods=["POST"])
@has_request_body(CreateRecipeCollectionRequest)
def create_recipe_collection():
    _Logger = logging.getLogger(__name__)
    _Handler = get_container().inject(CreateRecipeCollectionHandler)
    _Request: CreateRecipeCollectionRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.recipe_collection_already_exists:
        _Logger.warning(f"Recipe collection already exists: {_Request.name}")
        return business_rule_violation(
            f"A recipe collection with the name '{_Request.name}' already exists."
        )

    from dora_api.features.recipe_collections.get_recipe_collections import \
        GetRecipeCollectionsHandler
    _Dto = get_container().inject(GetRecipeCollectionsHandler).handle_by_id(
        _Response.new_recipe_collection_id
    )
    return created(
        _Response.new_recipe_collection_id,
        f"{RECIPE_COLLECTION_ROUTER.name}.{get_recipe_collections.__name__}",
        "recipe_collection_id",
        body = _Dto,
    )
