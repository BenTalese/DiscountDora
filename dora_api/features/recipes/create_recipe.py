import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.category import Category
from dora_api.domain.entities.cuisine import Cuisine
from dora_api.domain.entities.recipe import (
    ALLOWED_DIFFICULTY_VALUES,
    ALLOWED_STEPS_MODES,
    Recipe,
)
from dora_api.domain.entities.recipe_collection import RecipeCollection
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.meal_slots.slot_validation import (
    get_valid_slot_names, invalid_slot_message)
from dora_api.features.recipes.get_recipes import get_recipes
from dora_api.features.recipes.recipe_tag_access import set_tag_ids_for_recipe
from dora_api.features.recipes.recipe_tool_access import set_tool_ids_for_recipe
from dora_api.features.recipes.recipe_step_access import (
    StepWrite, replace_steps_for_recipe,
)
from dora_api.features.recipes.recipe_step_image_access import (
    StepImageWrite, replace_step_images_for_recipe,
)
from dora_api.features.recipes.recipe_section_access import (
    SectionWrite, replace_sections_for_recipe,
)
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation,
                                                  created,
                                                  entity_existence_failure,
                                                  entity_existence_failures)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (field_of, get_container,
                                           get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class CreateRecipeIngredientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock_item_id: UUID
    quantity: float | None = None
    unit: str | None = Field(default = None, max_length = 50)
    notes: str | None = Field(default = None, max_length = 255)
    # C-4 Chunk 6 — optional client-side identifier (any string) used by
    # `steps[].ingredient_client_ids` to point at this ingredient before the
    # server has assigned its UUID. Omit when no step references it.
    client_id: str | None = Field(default = None, max_length = 64)
    # C-4 Chunk 10 — optional section grouping; the client_id of one of the
    # sections in the same payload. Omit/null to leave in the implicit
    # "main" group.
    section_client_id: str | None = Field(default = None, max_length = 64)
    # Cookbook revision §1.9 — optional ingredients are ignored by the
    # cookability rule. Default false keeps the existing client contract
    # backward-compatible (omitting the field = required ingredient).
    is_optional: bool = False


class CreateRecipeStepRequest(BaseModel):
    """C-4 Chunk 6 — one structured step on a create payload.

    `client_id` is required (any string the client picks) so steps can
    refer to one another (parent_client_id) and to ingredients
    (ingredient_client_ids) before the server has issued real ids.
    """
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(min_length = 1, max_length = 64)
    parent_client_id: str | None = Field(default = None, max_length = 64)
    sequence: int = Field(default = 0, ge = 0)
    text: str = Field(min_length = 1)
    hint: str | None = None
    ingredient_client_ids: List[str] = Field(default_factory = list)
    tool_ids: List[UUID] = Field(default_factory = list)
    # C-4 Chunk 10 — optional section grouping; resolved against the sibling
    # `sections[]` entry with the same client_id.
    section_client_id: str | None = Field(default = None, max_length = 64)


class CreateRecipeSectionRequest(BaseModel):
    """C-4 Chunk 10 — a named section in the create payload."""
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(min_length = 1, max_length = 64)
    sequence: int = Field(default = 0, ge = 0)
    name: str = Field(min_length = 1, max_length = 255)


class CreateRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length = 1, max_length = 255)
    # C-4 Chunk 2: cuisine + category are FK vocabularies (single-select each).
    category_id: UUID | None = None
    cook_time_minutes: int | None = Field(default = None, ge = 0)
    cuisine_id: UUID | None = None
    difficulty: str | None = Field(default = None, max_length = 50)
    instructions: str | None = None
    nutrition: str | None = None
    prep_time_minutes: int | None = Field(default = None, ge = 0)
    recipe_collection_id: UUID | None = None
    servings: int | None = Field(default = None, ge = 1)
    # C-4 Chunk 7 — origin URL for imported recipes.
    source: str | None = Field(default = None, max_length = 2048)
    time_of_day: str | None = Field(default = None, max_length = 50)
    # C-4 Chunk 9 — simple nutrition (kcal). Gated on the C-cross
    # nutrition opt-in client-side; the server stores whatever's sent.
    kcal: int | None = Field(default = None, ge = 0, le = 100_000)
    ingredients: List[CreateRecipeIngredientRequest] = Field(default_factory = list)
    # C-4 Chunk 2 — dietary tag ids (FK to DietaryTag). Validated server-side
    # against existing rows; unknown ids surface as a 400.
    dietary_tag_ids: List[UUID] = Field(default_factory = list)
    # C-4 Chunk 5 — tool ids (FK to Tool).
    tool_ids: List[UUID] = Field(default_factory = list)
    # C-4 Chunk 5 — optional image as a data-URL string ("data:image/...;
    # base64,..."). Stored as UTF-8 bytes; served back via GET /recipes/<id>/
    # image. Capped to keep the row sane (~4MB raw image).
    image: str | None = Field(default = None, max_length = 6_000_000)
    # C-4 Chunk 6 — structured steps. Empty list = unstructured recipe
    # (cook-mode falls back to splitting `instructions` on newline). Each
    # step's `ingredient_client_ids` references its sibling ingredients via
    # the `client_id` field above.
    steps: List[CreateRecipeStepRequest] = Field(default_factory = list)
    # PROPOSAL_RECIPE_IMAGE_STEPS — explicit step payload selector. Closed
    # set validated below (R-010). Defaults to 'freeform'; the editor flips
    # to 'structured'/'image' as the user picks the mode.
    steps_mode: str = Field(default = "freeform", max_length = 16)
    # PROPOSAL_RECIPE_IMAGE_STEPS — ordered data-URL strings for the image
    # mode. Empty list when not in image mode. Cap mirrored from the
    # access helper.
    step_images: List[str] = Field(default_factory = list)
    # C-4 Chunk 10 — named sections (optional). When non-empty, the server
    # creates RecipeSection rows; ingredients and steps reference them by
    # `section_client_id`. Unreferenced sections still get created (empty
    # group) so the user can type the name first, then drop rows into it.
    sections: List[CreateRecipeSectionRequest] = Field(default_factory = list)


@dataclass(slots=True)
class CreateRecipeResponse:
    new_recipe_id: UUID = EMPTY_UUID
    recipe_already_exists: bool = False
    recipe_collection_not_found: bool = False
    cuisine_not_found: bool = False
    category_not_found: bool = False
    missing_stock_item_ids: tuple[UUID, ...] = ()
    invalid_tag_message: str | None = None
    invalid_step_message: str | None = None
    invalid_section_message: str | None = None
    invalid_vocabulary_message: str | None = None


class CreateRecipeHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateRecipeRequest) -> CreateRecipeResponse:
        # §1.7/§1.12 — closed-set vocabularies (R-010).
        if request.difficulty is not None and request.difficulty not in ALLOWED_DIFFICULTY_VALUES:
            return CreateRecipeResponse(
                invalid_vocabulary_message=(
                    f"Invalid difficulty '{request.difficulty}'. "
                    f"Allowed: {', '.join(ALLOWED_DIFFICULTY_VALUES)}."
                ),
            )
        # C-2.A — `time_of_day` is the household meal-slot vocabulary
        # (MealSlot table), validated at the boundary (R-010). Off-vocab
        # values are rejected on new writes; legacy stored values persist.
        if request.time_of_day is not None:
            _ValidSlots = get_valid_slot_names(self.repository)
            if request.time_of_day not in _ValidSlots:
                return CreateRecipeResponse(
                    invalid_vocabulary_message=invalid_slot_message(
                        request.time_of_day, _ValidSlots
                    ),
                )

        _RecipeName = EntityField(Recipe, Recipe.Fields.NAME)
        _ExistingRecipe: Recipe | None = (
            self.repository
            .get(Recipe)
            .one(_RecipeName.eq(request.name))
        )
        if _ExistingRecipe:
            return CreateRecipeResponse(recipe_already_exists = True)

        _Collection: RecipeCollection | None = None
        if request.recipe_collection_id:
            _Collection = self.repository.get(RecipeCollection).by_id(request.recipe_collection_id)
            if not _Collection:
                return CreateRecipeResponse(recipe_collection_not_found = True)

        _Cuisine: Cuisine | None = None
        if request.cuisine_id:
            _Cuisine = self.repository.get(Cuisine).by_id(request.cuisine_id)
            if not _Cuisine:
                return CreateRecipeResponse(cuisine_not_found = True)

        _Category: Category | None = None
        if request.category_id:
            _Category = self.repository.get(Category).by_id(request.category_id)
            if not _Category:
                return CreateRecipeResponse(category_not_found = True)

        _Ingredients: List[RecipeIngredient] = []
        _IngredientPairs: List[tuple[str | None, RecipeIngredient]] = []
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
                is_optional = _IngredientRequest.is_optional,
            )
            _Ingredients.append(_NewIngredient)
            _IngredientPairs.append((_IngredientRequest.client_id, _NewIngredient))

        if _MissingIds:
            return CreateRecipeResponse(missing_stock_item_ids = tuple(_MissingIds))

        # `add()` assigns the real id (uuid4), so the client→real map for
        # structured-step ingredient linkage must be built AFTER this loop.
        for _Ingredient in _Ingredients:
            self.repository.add(_Ingredient)
        _IngredientClientToReal: dict[str, UUID] = {
            client_id: ing.id
            for client_id, ing in _IngredientPairs
            if client_id
        }

        _NewRecipe = Recipe(
            available_meals = 0,
            category = _Category,
            cook_time_minutes = request.cook_time_minutes,
            cuisine = _Cuisine,
            difficulty = request.difficulty,
            image = request.image.encode("utf-8") if request.image else None,
            ingredients = _Ingredients,
            instructions = request.instructions,
            is_favourite = False,
            last_made_on = None,
            name = request.name,
            nutrition = request.nutrition,
            prep_time_minutes = request.prep_time_minutes,
            recipe_collection = _Collection,
            servings = request.servings,
            source = request.source,
            time_of_day = request.time_of_day,
            # C-4 Chunk 8 — singletons get NULL; the new-version endpoint
            # is the only path that populates this.
            version_group_id = None,
            kcal = request.kcal,
            steps_mode = request.steps_mode if request.steps_mode in ALLOWED_STEPS_MODES else "freeform",
            # FU-082 — stamp at write time so the cookbook "Recently
            # added" sort axis has a stable, recipe-owned timestamp.
            created_at = datetime.now(timezone.utc),
        )

        self.repository.add(_NewRecipe)
        # Save first so the recipe row exists before the tag FK insert.
        self.repository.save_changes()

        # C-4 Chunk 10 — insert sections, then back-fill ingredient
        # rows with their resolved section_id. Sections live as their
        # own table so the FK from RecipeIngredient.section_id is
        # satisfiable; the back-fill keeps the rest of the request
        # logic (steps replace below) on the same map.
        _SectionClientToReal: dict[str, UUID] = {}
        if request.sections:
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
                        _NewRecipe.id, _SectionWrites
                    ).items()
                }
            except ValueError as exc:
                return CreateRecipeResponse(
                    new_recipe_id=_NewRecipe.id,
                    invalid_section_message=str(exc),
                )
            # Back-fill section_id on the freshly-inserted ingredients.
            if _SectionClientToReal:
                from dora_api.app import db
                _IngTable = db.metadata.tables["RecipeIngredient"]
                for ing_req, (_cid, ing_ent) in zip(request.ingredients, _IngredientPairs):
                    if not ing_req.section_client_id:
                        continue
                    real = _SectionClientToReal.get(ing_req.section_client_id)
                    if real is None:
                        continue
                    db.session.execute(
                        _IngTable.update()
                        .where(_IngTable.c.id == ing_ent.id)
                        .values(section_id=real)
                    )
            self.repository.save_changes()

        if request.dietary_tag_ids or request.tool_ids:
            try:
                if request.dietary_tag_ids:
                    set_tag_ids_for_recipe(_NewRecipe.id, request.dietary_tag_ids)
                if request.tool_ids:
                    set_tool_ids_for_recipe(_NewRecipe.id, request.tool_ids)
            except ValueError as exc:
                # The recipe row stays — invalid tag/tool input shouldn't fail
                # the whole create; surface the bad id to the caller.
                return CreateRecipeResponse(
                    new_recipe_id=_NewRecipe.id,
                    invalid_tag_message=str(exc),
                )
            self.repository.save_changes()

        if request.steps:
            try:
                _StepWrites = [
                    StepWrite(
                        client_id=step.client_id,
                        parent_client_id=step.parent_client_id,
                        sequence=step.sequence,
                        text=step.text,
                        hint=step.hint,
                        ingredient_ids=[
                            _IngredientClientToReal[c]
                            for c in step.ingredient_client_ids
                            if c in _IngredientClientToReal
                        ],
                        tool_ids=list(step.tool_ids),
                        section_id=(
                            _SectionClientToReal.get(step.section_client_id)
                            if step.section_client_id else None
                        ),
                    )
                    for step in request.steps
                ]
                replace_steps_for_recipe(_NewRecipe.id, _StepWrites)
            except ValueError as exc:
                return CreateRecipeResponse(
                    new_recipe_id=_NewRecipe.id,
                    invalid_step_message=str(exc),
                )
            self.repository.save_changes()

        # PROPOSAL_RECIPE_IMAGE_STEPS — write step images last so the FK to
        # the just-created recipe is satisfied. The replace helper validates
        # the data-URL shape and per-recipe cap before any insert.
        if request.step_images:
            try:
                _ImageWrites = [
                    StepImageWrite(sequence=i, image_data_url=data_url)
                    for i, data_url in enumerate(request.step_images)
                ]
                replace_step_images_for_recipe(_NewRecipe.id, _ImageWrites)
            except ValueError as exc:
                return CreateRecipeResponse(
                    new_recipe_id=_NewRecipe.id,
                    invalid_step_message=str(exc),
                )
            self.repository.save_changes()

        return CreateRecipeResponse(new_recipe_id = _NewRecipe.id)


@RECIPE_ROUTER.route("", methods=["POST"])
@has_request_body(CreateRecipeRequest)
def create_recipe():
    _Logger = logging.getLogger(__name__)
    _Logger.info("Received request to create recipe.")
    _Handler = get_container().inject(CreateRecipeHandler)
    _Request: CreateRecipeRequest = get_request_body()
    _Response = _Handler.handle(_Request)

    if _Response.recipe_already_exists:
        _Logger.warning(f"Recipe already exists with name: {_Request.name}")
        return business_rule_violation(f"A recipe with the name '{_Request.name}' already exists.")

    if _Response.recipe_collection_not_found and _Request.recipe_collection_id:
        _Logger.warning(f"Recipe collection not found: {_Request.recipe_collection_id}")
        return entity_existence_failure(
            RecipeCollection.__name__,
            field_of(CreateRecipeRequest, 'recipe_collection_id'),
            _Request.recipe_collection_id,
        )

    if _Response.cuisine_not_found and _Request.cuisine_id:
        _Logger.warning(f"Cuisine not found: {_Request.cuisine_id}")
        return entity_existence_failure(
            Cuisine.__name__,
            field_of(CreateRecipeRequest, 'cuisine_id'),
            _Request.cuisine_id,
        )

    if _Response.category_not_found and _Request.category_id:
        _Logger.warning(f"Category not found: {_Request.category_id}")
        return entity_existence_failure(
            Category.__name__,
            field_of(CreateRecipeRequest, 'category_id'),
            _Request.category_id,
        )

    if _Response.missing_stock_item_ids:
        _Logger.warning(f"Stock items not found: {_Response.missing_stock_item_ids}")
        return entity_existence_failures(
            StockItem.__name__,
            field_of(CreateRecipeRequest, 'ingredients'),
            *_Response.missing_stock_item_ids,
        )

    if _Response.invalid_tag_message:
        _Logger.warning(f"Invalid recipe tag: {_Response.invalid_tag_message}")
        return bad_request(_Response.invalid_tag_message)

    if _Response.invalid_step_message:
        _Logger.warning(f"Invalid recipe step: {_Response.invalid_step_message}")
        return bad_request(_Response.invalid_step_message)

    if _Response.invalid_section_message:
        _Logger.warning(f"Invalid recipe section: {_Response.invalid_section_message}")
        return bad_request(_Response.invalid_section_message)

    if _Response.invalid_vocabulary_message:
        _Logger.warning(f"Invalid recipe vocabulary: {_Response.invalid_vocabulary_message}")
        return bad_request(_Response.invalid_vocabulary_message)

    _Logger.info(f"Successfully created recipe with ID: {_Response.new_recipe_id}")
    from dora_api.features.recipes.get_recipes import GetRecipesHandler
    _Dto = get_container().inject(GetRecipesHandler).handle_by_id(_Response.new_recipe_id)
    return created(
        _Response.new_recipe_id,
        f"{RECIPE_ROUTER.name}.{get_recipes.__name__}",
        "recipe_id",
        body = _Dto,
    )
