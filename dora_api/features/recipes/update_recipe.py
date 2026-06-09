import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.category import Category
from dora_api.domain.entities.cuisine import Cuisine
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.recipes.recipe_tag_access import set_tag_ids_for_recipe
from dora_api.features.recipes.recipe_tool_access import set_tool_ids_for_recipe
from dora_api.features.recipes.recipe_step_access import (
    StepWrite, replace_steps_for_recipe,
)
from dora_api.features.recipes.recipe_section_access import (
    SectionWrite, replace_sections_for_recipe,
)
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation,
                                                  entity_existence_failure,
                                                  entity_existence_failures,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class UpdateRecipeIngredientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock_item_id: UUID
    quantity: float | None = None
    unit: str | None = Field(default = None, max_length = 50)
    notes: str | None = Field(default = None, max_length = 255)
    # C-4 Chunk 6 — see CreateRecipeIngredientRequest.client_id. Optional
    # client-side identifier so `steps[].ingredient_client_ids` can point at
    # this row before the server hands back a real id.
    client_id: str | None = Field(default = None, max_length = 64)
    # C-4 Chunk 10 — optional section grouping; client_id of one of the
    # sections in the same payload, OR the existing section's UUID string
    # when leaving sections untouched. Null = unsectioned.
    section_client_id: str | None = Field(default = None, max_length = 64)


class UpdateRecipeStepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(min_length = 1, max_length = 64)
    parent_client_id: str | None = Field(default = None, max_length = 64)
    sequence: int = Field(default = 0, ge = 0)
    text: str = Field(min_length = 1)
    hint: str | None = None
    ingredient_client_ids: List[str] = Field(default_factory = list)
    tool_ids: List[UUID] = Field(default_factory = list)
    section_client_id: str | None = Field(default = None, max_length = 64)


class UpdateRecipeSectionRequest(BaseModel):
    """C-4 Chunk 10 — a named section on the update payload."""
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(min_length = 1, max_length = 64)
    sequence: int = Field(default = 0, ge = 0)
    name: str = Field(min_length = 1, max_length = 255)


class UpdateRecipeRequest(BaseModel):
    """Partial update — only fields present in the request body are applied.

    Pydantic's `model_fields_set` is used to distinguish 'not provided' from
    'explicitly null'. Default values are placeholders and never applied.
    """
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default = None, min_length = 1, max_length = 255)
    # C-4 Chunk 2: cuisine + category are FK vocabularies (resolved like
    # recipe_collection_id below). Explicit null clears the link.
    category_id: UUID | None = None
    cook_time_minutes: int | None = None
    cuisine_id: UUID | None = None
    difficulty: str | None = None
    instructions: str | None = None
    is_favourite: bool | None = None
    nutrition: str | None = None
    prep_time_minutes: int | None = None
    recipe_collection_id: UUID | None = None
    servings: int | None = None
    # C-4 Chunk 7 — origin URL for imported recipes. Explicit null clears.
    source: str | None = Field(default = None, max_length = 2048)
    time_of_day: str | None = None
    # C-4 Chunk 9 — simple nutrition (kcal). Explicit null clears.
    kcal: int | None = Field(default = None, ge = 0, le = 100_000)
    ingredients: List[UpdateRecipeIngredientRequest] | None = None
    # C-4 Chunk 2/5 — when present (even as an empty list), the full tag/tool
    # set is replaced. Omit the field to leave the existing set untouched.
    dietary_tag_ids: List[UUID] | None = None
    tool_ids: List[UUID] | None = None
    # C-4 Chunk 5 — data-URL image string; explicit null clears it. Omit to
    # leave the existing image untouched.
    image: str | None = Field(default = None, max_length = 6_000_000)
    # C-4 Chunk 6 — structured steps. When present (even as []), the full
    # step set is replaced. Omit to leave existing steps untouched. An empty
    # list clears all structure (recipe falls back to plain `instructions`).
    steps: List[UpdateRecipeStepRequest] | None = None
    # C-4 Chunk 10 — present (even as []) = replace the full section set.
    # Empty list clears all sections; ingredients/steps fall back to the
    # implicit "main" group via ON DELETE SET NULL. Omit to leave
    # existing sections untouched.
    sections: List[UpdateRecipeSectionRequest] | None = None


@dataclass(slots=True)
class UpdateRecipeResponse:
    recipe_not_found: bool = False
    recipe_already_exists: bool = False
    recipe_collection_not_found: bool = False
    cuisine_not_found: bool = False
    category_not_found: bool = False
    missing_stock_item_ids: tuple[UUID, ...] = ()
    invalid_tag_message: str | None = None
    invalid_step_message: str | None = None
    invalid_section_message: str | None = None


# Attributes that may safely be assigned from the request as-is, including
# explicit nulls for the nullable ones. `is_favourite` is handled separately
# because the entity column is NOT NULL — accepting null from a PATCH would
# turn a request-level oversight into a 500 at commit time. cuisine/category
# are FK relationships resolved separately below.
_NULLABLE_PLAIN_ATTRS = (
    "cook_time_minutes", "difficulty",
    "instructions", "nutrition", "prep_time_minutes",
    "servings", "source", "time_of_day", "kcal",
)


class UpdateRecipeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateRecipeRequest, recipe_id: UUID) -> UpdateRecipeResponse:
        _Recipe: Recipe | None = (
            self.repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
            .one(EntityField(Recipe, "id").eq(recipe_id))
        )
        if not _Recipe:
            return UpdateRecipeResponse(recipe_not_found = True)

        _SetFields = request.model_fields_set

        if "name" in _SetFields and request.name is not None:
            _NameField = EntityField(Recipe, Recipe.Fields.NAME)
            _SameName: Recipe | None = self.repository.get(Recipe).one(_NameField.eq(request.name))
            if _SameName and _SameName.id != recipe_id:
                return UpdateRecipeResponse(recipe_already_exists = True)
            _Recipe.name = request.name

        if "recipe_collection_id" in _SetFields:
            if request.recipe_collection_id is None:
                _Recipe.recipe_collection = None
            else:
                _Collection = self.repository.get(RecipeCollection).by_id(request.recipe_collection_id)
                if not _Collection:
                    return UpdateRecipeResponse(recipe_collection_not_found = True)
                _Recipe.recipe_collection = _Collection

        if "cuisine_id" in _SetFields:
            if request.cuisine_id is None:
                _Recipe.cuisine = None
            else:
                _Cuisine = self.repository.get(Cuisine).by_id(request.cuisine_id)
                if not _Cuisine:
                    return UpdateRecipeResponse(cuisine_not_found = True)
                _Recipe.cuisine = _Cuisine

        if "category_id" in _SetFields:
            if request.category_id is None:
                _Recipe.category = None
            else:
                _Category = self.repository.get(Category).by_id(request.category_id)
                if not _Category:
                    return UpdateRecipeResponse(category_not_found = True)
                _Recipe.category = _Category

        # C-4 Chunk 10 — sections replace first so the new ingredient/step
        # FKs can target the freshly-inserted rows. Empty list clears (rows
        # fall back to the implicit "main" group via ON DELETE SET NULL).
        _SectionClientToReal: dict[str, UUID] = {}
        _SectionsReplaced = False
        if "sections" in _SetFields and request.sections is not None:
            try:
                _SectionWrites = [
                    SectionWrite(
                        client_id=section.client_id,
                        sequence=section.sequence,
                        name=section.name,
                    )
                    for section in request.sections
                ]
                _SectionClientToReal = {
                    str(k): v
                    for k, v in replace_sections_for_recipe(
                        recipe_id, _SectionWrites
                    ).items()
                }
                _SectionsReplaced = True
            except ValueError as exc:
                return UpdateRecipeResponse(invalid_section_message=str(exc))

        def _resolve_section(token: str | None) -> UUID | None:
            if not token:
                return None
            if token in _SectionClientToReal:
                return _SectionClientToReal[token]
            # Caller is leaving sections untouched and passed an existing
            # section UUID directly — trust it; the FK + ondelete=SET NULL
            # already protects us from dangling references.
            try:
                return UUID(token)
            except (ValueError, TypeError):
                return None

        _IngredientClientToReal: dict[str, UUID] = {}
        if "ingredients" in _SetFields and request.ingredients is not None:
            _NewIngredients: List[RecipeIngredient] = []
            _NewPairs: List[tuple[str | None, RecipeIngredient]] = []
            _MissingIds: List[UUID] = []
            for _IngredientRequest in request.ingredients:
                _StockItem = self.repository.get(StockItem).by_id(_IngredientRequest.stock_item_id)
                if not _StockItem:
                    _MissingIds.append(_IngredientRequest.stock_item_id)
                    continue
                _NewIngredient = RecipeIngredient(
                    notes = _IngredientRequest.notes,
                    quantity = _IngredientRequest.quantity,
                    stock_item = _StockItem,
                    unit = _IngredientRequest.unit,
                    section_id = _resolve_section(_IngredientRequest.section_client_id),
                )
                _NewIngredients.append(_NewIngredient)
                _NewPairs.append((_IngredientRequest.client_id, _NewIngredient))
            if _MissingIds:
                return UpdateRecipeResponse(missing_stock_item_ids = tuple(_MissingIds))
            for _Ingredient in _NewIngredients:
                self.repository.add(_Ingredient)
            _Recipe.ingredients = _NewIngredients
            _IngredientClientToReal = {
                cid: ing.id for cid, ing in _NewPairs if cid
            }

        for _Attr in _NULLABLE_PLAIN_ATTRS:
            if _Attr in _SetFields:
                setattr(_Recipe, _Attr, getattr(request, _Attr))

        # is_favourite is bool-non-nullable on the entity; ignore explicit nulls.
        if "is_favourite" in _SetFields and request.is_favourite is not None:
            _Recipe.is_favourite = request.is_favourite

        # C-4 Chunk 5 — image: explicit null clears, a data-URL string sets it.
        if "image" in _SetFields:
            _Recipe.image = request.image.encode("utf-8") if request.image else None

        # C-4 Chunk 2/5 — replace the tag/tool set when explicitly provided.
        # Empty list clears; omitted field leaves untouched.
        if "dietary_tag_ids" in _SetFields and request.dietary_tag_ids is not None:
            try:
                set_tag_ids_for_recipe(recipe_id, request.dietary_tag_ids)
            except ValueError as exc:
                return UpdateRecipeResponse(invalid_tag_message=str(exc))
        if "tool_ids" in _SetFields and request.tool_ids is not None:
            try:
                set_tool_ids_for_recipe(recipe_id, request.tool_ids)
            except ValueError as exc:
                return UpdateRecipeResponse(invalid_tag_message=str(exc))

        # C-4 Chunk 6 — steps replace. Ingredient client_ids resolve via the
        # new-ingredients map; any token that didn't match (because the
        # client is keeping existing ingredients untouched) is parsed as a
        # raw UUID and trusted to the access helper's per-recipe validation.
        if "steps" in _SetFields and request.steps is not None:
            def _resolve_ing(token: str) -> UUID | None:
                if token in _IngredientClientToReal:
                    return _IngredientClientToReal[token]
                try:
                    return UUID(token)
                except (ValueError, TypeError):
                    return None
            try:
                _StepWrites = [
                    StepWrite(
                        client_id=step.client_id,
                        parent_client_id=step.parent_client_id,
                        sequence=step.sequence,
                        text=step.text,
                        hint=step.hint,
                        ingredient_ids=[
                            resolved
                            for resolved in (_resolve_ing(c) for c in step.ingredient_client_ids)
                            if resolved is not None
                        ],
                        tool_ids=list(step.tool_ids),
                        section_id=_resolve_section(step.section_client_id),
                    )
                    for step in request.steps
                ]
                replace_steps_for_recipe(recipe_id, _StepWrites)
            except ValueError as exc:
                return UpdateRecipeResponse(invalid_step_message=str(exc))

        self.repository.save_changes()
        return UpdateRecipeResponse()


@RECIPE_ROUTER.route("<recipe_id>", methods=["PATCH"])
@has_request_body(UpdateRecipeRequest)
def update_recipe(recipe_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to update recipe.")
    _Handler = get_container().inject(UpdateRecipeHandler)
    _Request: UpdateRecipeRequest = get_request_body()
    _Response = _Handler.handle(_Request, recipe_id)

    if _Response.recipe_not_found:
        _Logger.warning(f"Recipe not found with ID: {recipe_id}")
        return not_found(Recipe.__name__, recipe_id)

    if _Response.recipe_already_exists:
        _Logger.warning(f"Recipe already exists with name: {_Request.name}")
        return business_rule_violation(f"A recipe with the name '{_Request.name}' already exists.")

    if (_Response.recipe_collection_not_found
            and "recipe_collection_id" in _Request.model_fields_set
            and _Request.recipe_collection_id is not None):
        _Logger.warning(f"Recipe collection not found: {_Request.recipe_collection_id}")
        return entity_existence_failure(
            RecipeCollection.__name__,
            field_of(UpdateRecipeRequest, 'recipe_collection_id'),
            _Request.recipe_collection_id,
        )

    if (_Response.cuisine_not_found
            and "cuisine_id" in _Request.model_fields_set
            and _Request.cuisine_id is not None):
        _Logger.warning(f"Cuisine not found: {_Request.cuisine_id}")
        return entity_existence_failure(
            Cuisine.__name__,
            field_of(UpdateRecipeRequest, 'cuisine_id'),
            _Request.cuisine_id,
        )

    if (_Response.category_not_found
            and "category_id" in _Request.model_fields_set
            and _Request.category_id is not None):
        _Logger.warning(f"Category not found: {_Request.category_id}")
        return entity_existence_failure(
            Category.__name__,
            field_of(UpdateRecipeRequest, 'category_id'),
            _Request.category_id,
        )

    if _Response.missing_stock_item_ids:
        _Logger.warning(f"Stock items not found: {_Response.missing_stock_item_ids}")
        return entity_existence_failures(
            StockItem.__name__,
            field_of(UpdateRecipeRequest, 'ingredients'),
            *_Response.missing_stock_item_ids,
        )

    if _Response.invalid_tag_message:
        _Logger.warning(f"Invalid recipe tag on update: {_Response.invalid_tag_message}")
        return bad_request(_Response.invalid_tag_message)

    if _Response.invalid_step_message:
        _Logger.warning(f"Invalid recipe step on update: {_Response.invalid_step_message}")
        return bad_request(_Response.invalid_step_message)

    if _Response.invalid_section_message:
        _Logger.warning(f"Invalid recipe section on update: {_Response.invalid_section_message}")
        return bad_request(_Response.invalid_section_message)

    _Logger.info(f"Successfully updated recipe with ID: {recipe_id}")
    return no_content()
