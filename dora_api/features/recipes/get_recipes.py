import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.dietary_tag import DietaryTag
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.recipe_tags import RECIPE_TAG_DISCLAIMER
from dora_api.domain.recipe_cookability import (cookability_state,
                                                 missing_count_for,
                                                 missing_stock_item_names_for,
                                                 unlinked_count_for)
from dora_api.domain.stock_status import (is_low_stock, is_missing)
from dora_api.features.recipes.recipe_tag_access import (
    find_recipe_ids_with_all_tags, find_recipe_ids_with_any_tags,
    get_tag_ids_for_recipes,
)
from dora_api.features.recipes.recipe_tool_access import (
    find_recipe_ids_with_all_tools, find_recipe_ids_with_any_tools,
    get_tool_ids_for_recipes,
)
from dora_api.features.recipes.recipe_step_access import (
    get_steps_for_recipe, has_structured_steps_for_recipes,
)
from dora_api.features.recipes.recipe_step_image_access import (
    get_step_image_metadata_for_recipe, has_step_images_for_recipes,
    get_step_image_bytes,
)
from dora_api.features.recipes.recipe_section_access import (
    get_section_count_for_recipes, get_sections_for_recipe,
)
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import bad_request, not_found, ok, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


@dataclass(frozen=True, slots=True)
class RecipeIngredientDto:
    recipe_ingredient_id: UUID
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — nullable so unlinked
    # (paste-imported, no fuzzy match) rows round-trip. The SPA renders
    # unlinked rows with an "Unlinked · Link" pill. When null,
    # ``stock_item_name``, ``stock_level_id``, ``stock_location_id``,
    # ``stock_location_name`` are all null; ``raw_text`` carries the
    # ingredient label; ``is_missing`` / ``is_low_stock`` are False (we
    # can't say what's missing about an ingredient we haven't linked).
    stock_item_id: UUID | None
    stock_item_name: str | None
    stock_level_id: UUID | None
    # Direct location only — the frontend resolves the full breadcrumb via
    # the cached locations tree so recipe queries stay cheap.
    stock_location_id: UUID | None
    stock_location_name: str | None
    quantity: float | None
    unit: str | None
    notes: str | None
    # Server-derived stock status for this ingredient (§3.1 contract), so the
    # client never matches a stock-level name to decide cookability.
    is_missing: bool
    is_low_stock: bool
    # nullable section grouping. NULL = implicit "main"
    # group; the client uses this to bucket ingredients under the named
    # section headers from `RecipeDto.sections`.
    section_id: UUID | None
    # Cookbook revision §1.9 — optional ingredients. The recipe-level
    # `cookable` rollup and `missing_stock_item_names` both ignore
    # optional rows; they're surfaced here only so the edit dialog,
    # picker modal, and cook-mode UI can render them differently.
    is_optional: bool = False
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — the ingredient text as
    # pasted / imported. Persists even when linked; the SPA prefers it
    # for the label when non-empty ("1 pound ground turkey" is more
    # informative than "ground turkey").
    raw_text: str | None = None

    @classmethod
    def from_entity(cls, ingredient: RecipeIngredient) -> 'RecipeIngredientDto':
        _Item = ingredient.stock_item
        _Loc = _Item.stock_location if _Item else None
        _Level = _Item.stock_level if _Item else None
        return RecipeIngredientDto(
            recipe_ingredient_id = ingredient.id,
            stock_item_id = _Item.id if _Item else None,
            stock_item_name = _Item.name if _Item else None,
            stock_level_id = _Level.id if _Level else None,
            stock_location_id = _Loc.id if _Loc else None,
            stock_location_name = _Loc.name if _Loc else None,
            quantity = ingredient.quantity,
            unit = ingredient.unit,
            notes = ingredient.notes,
            is_missing = is_missing(_Level) if _Item else False,
            is_low_stock = is_low_stock(_Level) if _Item else False,
            section_id = getattr(ingredient, "section_id", None),
            is_optional = getattr(ingredient, "is_optional", False),
            raw_text = getattr(ingredient, "raw_text", None),
        )


@dataclass(frozen=True, slots=True)
class RecipeVersionSiblingDto:
    """C-4 Chunk 8 — a light view of a sibling version. The detail endpoint
    embeds an array of these so the UI can render a "Versions" card
    without a second round-trip; the fields are the minimum needed for the
    card row (name + last-made + meals-on-hand)."""
    recipe_id: UUID
    name: str
    last_made_on: date | None
    available_meals: int


@dataclass(frozen=True, slots=True)
class RecipeStepDto:
    """C-4 Chunk 6 — one structured step or sub-step.

    Flat shape; the frontend reassembles the tree from `parent_step_id`.
    `ingredient_ids` references the recipe's own `RecipeIngredient` rows
    (highlight which row this step uses); `tool_ids` references the Tool
    vocab.
    """
    step_id: UUID
    parent_step_id: UUID | None
    sequence: int
    text: str
    hint: str | None
    ingredient_ids: List[UUID]
    tool_ids: List[UUID]
    # top-level steps may belong to a section; NULL = main.
    # Sub-steps carry the same section_id as their parent for cheap reads.
    section_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RecipeSectionDto:
    """C-4 Chunk 10 — a named group within a recipe (DEC-3 option A).

    Sections are optional; a recipe with zero sections renders the same
    as it always did, with all ingredients/steps in the implicit "main"
    group (their `section_id` is NULL).
    """
    section_id: UUID
    sequence: int
    name: str


@dataclass(frozen=True, slots=True)
class RecipeNutritionDto:
    """FU-635 chunk 6 — complex-mode nutrition rolled up from the ingredients'
    linked foods. Detail endpoint only, and only while the install is in
    complex mode; `null` otherwise.

    Always carries its coverage (`counted_count` / `total_count` + the
    per-reason `uncounted` map) so the client can't render a partial total as
    a complete one — the owner's call was "partials shown and marked", never
    hidden.
    """
    basis: str                  # 'serving' | 'recipe' (no servings typed in)
    servings: int | None
    kcal: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    counted_count: int
    total_count: int
    uncounted: dict
    # FU-637 — whether coverage is high enough to *judge* the recipe on (rank
    # it, or exclude it from a "≤ N kcal" search). Display never gates on this;
    # a thin estimate is still shown, with its coverage. The threshold is a
    # domain constant and stays server-side (R-003).
    is_reliable: bool = False


@dataclass(frozen=True, slots=True)
class RecipeDto:
    recipe_id: UUID
    name: str
    available_meals: int
    unallocated_meals: int
    # Sum of future, un-consumed meal-plan servings for this recipe (the raw
    # commitment — NOT floored, unlike unallocated_meals). Lets the UI show a
    # shortfall (committed > available) in red. Hydrated post-query.
    committed_meals: int
    # "haven't had in a while" (last_made_on NULL or older than the
    # household 21-day window) + how often this recipe appears across meal
    # plans ("frequently planned"). Both hydrated post-query — the server owns
    # the window + the count (R-003); the client just renders the trays.
    not_made_recently: bool
    plan_count: int
    # true iff at least one MealPlanEntry for this recipe is
    # scheduled today or later AND not yet consumed. Server-owned (R-003)
    # so the cookbook's "Planned" / "Not planned" filter doesn't need to
    # walk every meal plan client-side. Hydrated alongside the existing
    # `committed_meals` derivation in `_hydrate_unallocated` (same query
    # — zero extra round-trip).
    is_planned: bool
    # cuisine + category are FK vocabularies. The id drives the
    # edit-form selects + client filters; the name is carried for cheap
    # display (card subtitle, search, export) without a client-side join.
    cuisine_id: UUID | None
    cuisine_name: str | None
    category_id: UUID | None
    category_name: str | None
    cook_time_minutes: int | None
    difficulty: str | None
    instructions: str | None
    is_favourite: bool
    last_made_on: date | None
    prep_time_minutes: int | None
    recipe_collection_id: UUID | None
    servings: int | None
    # origin URL when the recipe was imported.
    source: str | None
    time_of_day: str | None
    # version sibling group. NULL means singleton. List
    # endpoint sets `version_group_id` (cheap); detail endpoint also
    # populates `version_siblings[]` (the other recipes sharing the id).
    version_group_id: UUID | None
    # simple nutrition (kcal). Stored per-recipe; the
    # client gates the render on the C-cross nutrition opt-in. NULL when
    # the user hasn't typed one.
    kcal: int | None
    # when the recipe was added to this household. Drives the
    # cookbook "Recently added" sort axis. Never null on a row that came
    # through the create handlers (which stamp it) or through the
    # backfill migration f9d3a7c2b5e8.
    created_at: datetime | None
    ingredients: List[RecipeIngredientDto]
    # Server-owned cookability — computed once from the already-loaded
    # ingredient tree (§3.2 state-ownership refactor).
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4: ``cookable`` is now tri-state
    # (bool | None). ``None`` fires when any required ingredient is
    # unlinked; the SPA renders the badge dimmed with a "link
    # ingredients to check" tooltip. ``missing_count`` and
    # ``missing_stock_item_names`` count only LINKED-missing rows, so
    # they can safely be zero / empty on a None-cookable recipe.
    missing_count: int
    cookable: bool | None
    # Distinct, alphabetised names of the missing stock items — lets the
    # client render a "Missing: flour, eggs" hint without rejoining the
    # ingredient tree or the stock-level table.
    missing_stock_item_names: List[str]
    # whether the recipe has an image (the bytes are served via
    # GET /recipes/<id>/image, never inlined in list/detail JSON).
    has_image: bool
    # RD-29 — free-text personal notes about the recipe (cook's own
    # commentary). Surfaced in cook mode under the steps; NULL when unset.
    notes: str | None = None
    # IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — count of REQUIRED ingredients
    # whose ``stock_item_id`` is null. Drives the recipe-detail
    # "N ingredients need linking" prompt and the shopping-list
    # "add missing" flow's linking-first message.
    unlinked_ingredient_count: int = 0
    # dietary tag + tool ids. Empty list when none. Hydrated by
    # the handler after the base query — mutable so `from_entity` stays
    # agnostic of association loading.
    dietary_tag_ids: List[UUID] = field(default_factory=list)
    tool_ids: List[UUID] = field(default_factory=list)
    # structured steps. The list endpoint sets only
    # `has_structured_steps` (cheap existence check); detail hydrates
    # `steps[]` from the link tables. Empty steps + has_structured_steps
    # false ⇒ recipe is unstructured; cook-mode falls back to splitting
    # `instructions` on newline.
    has_structured_steps: bool = False
    steps: List['RecipeStepDto'] = field(default_factory=list)
    # populated only by `handle_by_id` (detail). List endpoint
    # leaves this empty; the client uses `version_group_id` on the list DTO
    # to know whether siblings exist at all.
    version_siblings: List['RecipeVersionSiblingDto'] = field(default_factory=list)
    # server-derived cost estimate (DEC-5). Populated only
    # on the detail endpoint and only when at least one ingredient has
    # a linked product offer; client gates render on the C-cross money
    # opt-in. NULL when no estimate could be computed (no linked
    # products in the recipe).
    estimated_cost: float | None = None
    # Companion to estimated_cost: count of ingredients we *couldn't*
    # price (no linked product / no current offer). Lets the UI add a
    # "based on N of M ingredients" disclaimer so the estimate is read
    # as an estimate, not a quote.
    estimated_cost_priced_count: int = 0
    estimated_cost_total_count: int = 0
    # named sections (DEC-3 option A). The list endpoint
    # populates only `section_count` (cheap), the detail endpoint also
    # hydrates `sections[]`. Empty sections + section_count == 0 ⇒ the
    # recipe is flat; ingredients/steps render under no header.
    section_count: int = 0
    sections: List['RecipeSectionDto'] = field(default_factory=list)
    # C-waste W4 — number of this recipe's ingredients (non-optional) that
    # are currently in stock and either expired or expiring within the
    # filter's horizon. Populated only when the request asked for the
    # filter (`?expiring_within_days=N`); zero otherwise. The cookbook
    # surfaces a "Uses N expiring" badge from this number.
    expiring_ingredient_count: int = 0
    # PROPOSAL_RECIPE_IMAGE_STEPS — which step payload to render. Server-
    # owned; replaces the implicit "has structured rows?" detection so
    # 'image' is a first-class peer. Default 'freeform' for new recipes.
    steps_mode: str = "freeform"
    # Cheap existence flag mirrored from has_structured_steps. Populated
    # by the list hydration (`_hydrate_has_step_images`); detail returns
    # full metadata via `step_images[]` below.
    has_step_images: bool = False
    # PROPOSAL_RECIPE_IMAGE_STEPS — ordered image metadata for the detail
    # endpoint only. The list endpoint leaves this empty; bytes are never
    # inlined either way (the SPA loads each via the dedicated bytes
    # endpoint at `/recipes/<id>/step-images/<image_id>`).
    step_images: List['RecipeStepImageDto'] = field(default_factory=list)
    # FU-635 — complex-mode nutrition rollup: the full breakdown + coverage,
    # for the recipe detail card. NULL outside complex mode.
    nutrition: 'RecipeNutritionDto | None' = None
    # FU-637 — the *effective* per-serving kcal for the install's current mode
    # (typed number in simple, rollup in complex), so no client re-derives
    # "which field, and may I trust it" (R-003). Distinct from `kcal` above,
    # which is the stored value the editor writes. NULL when there's no figure
    # — including a complex rollup with no servings typed in, where a
    # per-serving number would have to be invented.
    kcal_per_serving: float | None = None
    # Whether `kcal_per_serving` may be used to *judge* the recipe (filter it
    # out of a "≤ N kcal" search, rank it) as opposed to just display it.
    kcal_is_reliable: bool = False

    @classmethod
    def from_entity(cls, recipe: Recipe, dietary_tag_ids: list[UUID] | None = None, unallocated_meals: int | None = None) -> 'RecipeDto':
        _Available = recipe.available_meals or 0
        _IngDtos = [RecipeIngredientDto.from_entity(i) for i in (recipe.ingredients or [])]
        # Distinct missing stock items via the shared cookability rule (R-003) —
        # an ingredient listed on multiple rows is still one shopping line.
        _Missing = missing_count_for(recipe.ingredients)
        # Tri-state cookability (Chunk 4): None fires when any required
        # ingredient is unlinked. Rule owned by ``cookability_state``.
        _Cookable = cookability_state(recipe.ingredients)
        _Unlinked = unlinked_count_for(recipe.ingredients)
        return RecipeDto(
            recipe_id = recipe.id,
            name = recipe.name,
            available_meals = _Available,
            unallocated_meals = _Available if unallocated_meals is None else unallocated_meals,
            committed_meals = 0,
            not_made_recently = False,
            plan_count = 0,
            is_planned = False,
            cuisine_id = recipe.cuisine.id if recipe.cuisine else None,
            cuisine_name = recipe.cuisine.name if recipe.cuisine else None,
            category_id = recipe.category.id if recipe.category else None,
            category_name = recipe.category.name if recipe.category else None,
            cook_time_minutes = recipe.cook_time_minutes,
            difficulty = recipe.difficulty,
            instructions = recipe.instructions,
            is_favourite = recipe.is_favourite,
            last_made_on = recipe.last_made_on,
            prep_time_minutes = recipe.prep_time_minutes,
            recipe_collection_id = recipe.recipe_collection.id if recipe.recipe_collection else None,
            servings = recipe.servings,
            source = recipe.source,
            time_of_day = recipe.time_of_day,
            version_group_id = recipe.version_group_id,
            kcal = recipe.kcal,
            created_at = recipe.created_at,
            ingredients = _IngDtos,
            missing_count = _Missing,
            cookable = _Cookable,
            missing_stock_item_names = missing_stock_item_names_for(recipe.ingredients),
            unlinked_ingredient_count = _Unlinked,
            # `image` is now a deferred column; accessing
            # `recipe.image` here would trigger N+1 lazy loads on the
            # list path. Default False and let the handler hydrate
            # via a bulk SELECT below.
            has_image = False,
            dietary_tag_ids = dietary_tag_ids or [],
            steps_mode = recipe.steps_mode or "freeform",
            notes = getattr(recipe, "notes", None),
        )


@dataclass(frozen=True, slots=True)
class RecipeStepImageDto:
    """PROPOSAL_RECIPE_IMAGE_STEPS — ordered image metadata. The actual
    bytes live behind `GET /recipes/<recipe_id>/step-images/<image_id>`
    (mirrors the dish-image pattern) so DTO payloads stay slim."""
    image_id: UUID
    sequence: int


_FIELD_MAP: dict[str, EntityField] = {
    "recipe_id": EntityField(Recipe, "id"),
    "recipe_collection_id": EntityField(Recipe, "_recipe_collection_id"),
    # exposed so the cookbook can sort/filter by "Recently added"
    # via the standard `sort=created_at:desc` query string if it ever moves
    # off the client-side sort. The client sort uses the DTO field
    # directly; this entry lets API consumers do the same server-side.
    "created_at": EntityField(Recipe, Recipe.Fields.CREATED_AT),
}


@dataclass(frozen=True, slots=True)
class RecipeFilters:
    """Independent recipe filters that compose with AND.

    - tags_include : recipe must carry every tag in this list.
    - tags_exclude : recipe must carry none of the tags in this list.
    - ingredient_exclude : recipe must not have an ingredient whose stock
      item name contains any of the substrings (case-insensitive). Lets
      users say "free from egg" without us having to maintain an allergen
      taxonomy.
    - cookable : when True, only recipes with nothing missing (the same
      `missing_count == 0` the DTO exposes); when False, only recipes with
      at least one missing ingredient. ``None`` = no constraint.
    - max_missing : recipe must have at most this many missing ingredients.
      (State-ownership §3.3 — lets the overview query "Missing ≤ N" instead of
      fetching every recipe + the whole pantry to filter in the browser.)
    - expiring_within_days : when set, recipe must use at least one
      in-stock ingredient whose expiry is within the window. The
      cookbook "Uses expiring ingredients" filter (C-waste W4) sets this
      to 14; the predicate is pushed to the server so no cross-entity
      computation lives on the client (R-003).
    """
    tags_include: tuple[str, ...] = ()
    tags_exclude: tuple[str, ...] = ()
    tools_include: tuple[str, ...] = ()
    tools_exclude: tuple[str, ...] = ()
    ingredient_exclude: tuple[str, ...] = ()
    cookable: bool | None = None
    max_missing: int | None = None
    expiring_within_days: int | None = None

    @property
    def is_empty(self) -> bool:
        return not (
            self.tags_include
            or self.tags_exclude
            or self.tools_include
            or self.tools_exclude
            or self.ingredient_exclude
            or self.cookable is not None
            or self.max_missing is not None
            or self.expiring_within_days is not None
        )

    @property
    def needs_cookability(self) -> bool:
        """True when a filter axis requires per-recipe missing counts."""
        return self.cookable is not None or self.max_missing is not None

    def matches_cookability(self, missing: int, unlinked: int) -> bool:
        """Whether a recipe with ``missing`` linked-missing ingredients and
        ``unlinked`` unlinked-required ingredients passes the cookability
        axes.

        IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 tri-state semantics: a recipe
        with any unlinked required ingredient reads as cookability
        ``None`` (unknown). ``?cookable=true`` and ``?cookable=false``
        both exclude None recipes — the filter answers "definitely yes"
        or "definitely no", not "I don't know". ``?max_missing=N``
        similarly excludes unknown recipes because the count is
        meaningless when some required ingredients aren't linked.
        """
        if unlinked > 0:
            # Tri-state None — excluded from every cookability axis.
            if self.cookable is not None or self.max_missing is not None:
                return False
            return True
        if self.cookable is True and missing != 0:
            return False
        if self.cookable is False and missing == 0:
            return False
        if self.max_missing is not None and missing > self.max_missing:
            return False
        return True


def load_expiring_stock_item_ids(
    repository, horizon_days: int,
) -> set[UUID]:
    """Stock items whose expiry is within the horizon (expired included).

    Reused by the cookbook "Uses expiring ingredients" filter and its
    DTO hydration. Mirrors the predicate in
    `GetWasteRescueHandler.handle()` — same definition of "at risk"
    across the rescue feed and the cookbook surface (R-003).
    """
    from datetime import timedelta as _timedelta
    from dora_api.features.app_settings.clock import household_today as _household_today
    if horizon_days < 0:
        return set()
    # R-021 — at-risk horizon uses household-tz today.
    cutoff = _household_today(repository) + _timedelta(days=horizon_days)
    items = repository.get(StockItem).all(
        EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).is_not_null()
        & EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).lte(cutoff)
    )
    return {i.id for i in items}


def count_expiring_ingredients_per_recipe(
    repository, horizon_days: int,
) -> tuple[set[UUID], dict[UUID, int]]:
    """`(at_risk_item_ids, expiring_count_by_recipe_id)` over the horizon.

    The count ignores optional ingredients so the result matches the
    rescue feed's recipe ranking (cookbook revision §1.9 / R-003).
    Recipes whose count is zero are omitted from the dict, so callers
    can `.get(rid, 0)` for hydration and `set(d.keys())` for the
    restriction filter.
    """
    at_risk_ids = load_expiring_stock_item_ids(repository, horizon_days)
    if not at_risk_ids:
        return at_risk_ids, {}
    recipes = (
        repository
        .get(Recipe)
        .include(Recipe.Fields.INGREDIENTS)
            .then_include(RecipeIngredient.Fields.STOCK_ITEM)
        .all()
    )
    counts: dict[UUID, int] = {}
    for recipe in recipes:
        n = 0
        for ing in (recipe.ingredients or []):
            item = ing.stock_item
            if item is None:
                continue
            if getattr(ing, "is_optional", False):
                continue
            if item.id in at_risk_ids:
                n += 1
        if n > 0:
            counts[recipe.id] = n
    return at_risk_ids, counts


def load_recipe_cookability(
    repository,
) -> dict[UUID, tuple[int, int, int]]:
    """Map every recipe id -> ``(missing_count, ingredient_count, unlinked_count)``.

    One eager-loaded query, shared by the ``?cookable`` / ``?max_missing`` recipe
    filter and the dashboard's ``cookable_count`` so the cookability rule lives in
    one place (R-003, via :func:`missing_count_for`).

    * ``missing_count`` — distinct linked stock items missing (§3.2).
    * ``ingredient_count`` — total ingredient rows on the recipe.
    * ``unlinked_count`` — required ingredients with no ``stock_item_id``
      (Chunk 4). Callers gate the cookable-now count on this being zero:
      a recipe with any unlinked required ingredient is tri-state None,
      not True, and is excluded from the dashboard tally.
    """
    recipes = (
        repository
        .get(Recipe)
        .include(Recipe.Fields.INGREDIENTS)
            .then_include(RecipeIngredient.Fields.STOCK_ITEM)
            .then_include(StockItem.Fields.STOCK_LEVEL)
        .all()
    )
    return {
        r.id: (
            missing_count_for(r.ingredients),
            len(r.ingredients or []),
            unlinked_count_for(r.ingredients),
        )
        for r in recipes
    }


class GetRecipesHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository
        # Populated by `_restrict_query` when the C-waste cookbook filter
        # is active; consumed by `_hydrate_expiring_count` so the count
        # query runs once per request.
        self._expiring_counts: dict[UUID, int] = {}

    def _base_query(self):
        return (
            self.repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
                .then_include(RecipeIngredient.Fields.STOCK_ITEM)
                .then_include(StockItem.Fields.STOCK_LEVEL)
            .include(Recipe.Fields.INGREDIENTS)
                .then_include(RecipeIngredient.Fields.STOCK_ITEM)
                .then_include(StockItem.Fields.STOCK_LOCATION)
            .include(Recipe.Fields.RECIPE_COLLECTION)
            # cuisine + category flipped to noload; RecipeDto reads
            # both, so every list/detail hit must eager-load them here.
            .include(Recipe.Fields.CUISINE)
            .include(Recipe.Fields.CATEGORY)
        )

    def _ingredient_excluded_recipe_ids(self, terms: tuple[str, ...]) -> set[UUID]:
        """Recipe ids that have at least one ingredient whose stock item
        name contains any of the (case-insensitive) substrings. Returns
        an empty set for empty input — caller checks before subtracting.
        """
        if not terms:
            return set()
        normalised = [t.strip().lower() for t in terms if t.strip()]
        if not normalised:
            return set()
        # Walk ingredients with stock-item names loaded — a single query
        # via the eager include. We trade a full scan of the recipe-
        # ingredient join for simplicity; the personal-use scale doesn't
        # justify a denormalised search column yet.
        ingredients: list[RecipeIngredient] = (
            self.repository.get(RecipeIngredient)
            .include(RecipeIngredient.Fields.STOCK_ITEM)
            .all()
        )
        denied: set[UUID] = set()
        for ing in ingredients:
            item = ing.stock_item
            if item is None or not item.name:
                continue
            name_lower = item.name.lower()
            if any(term in name_lower for term in normalised):
                # `_recipe_id` is the FK column on the mapping; the
                # entity itself doesn't carry a `recipe_id` attribute.
                fk = getattr(ing, "_recipe_id", None) or getattr(ing, "recipe_id", None)
                if fk is not None:
                    denied.add(fk)
        return denied

    def _restrict_query(self, query, filters: RecipeFilters):
        """Resolve the filter axes into a single `id IN (...)` constraint
        applied to the page query. Returns the (possibly unchanged) query
        plus a boolean that's True when the filter set guarantees an empty
        result (e.g. `tags_include` matched zero recipes), so the caller can
        short-circuit the paginate."""
        if filters.is_empty:
            return query, False

        # Relationship-dependent maps are built FIRST. SQLAlchemy's
        # identity map hands already-loaded instances back to later
        # queries in the same session, so if the plain id-universe load
        # below ran first, its noload-empty `ingredients` collections
        # would poison these eager loads: every recipe would count
        # (0, 0, 0), silently turning `?cookable=true` into "keep all",
        # `?cookable=false` into "keep none", and the expiring filter
        # into an empty page (bug found by test_recipe_router.py,
        # 2026-07-10).
        cookability: dict[UUID, tuple[int, int, int]] | None = None
        if filters.needs_cookability:
            # `?cookable` matches the DTO `cookable` field exactly (missing == 0
            # AND every required ingredient linked, so an empty recipe is
            # cookable); `?max_missing=N` keeps recipes with at most N missing
            # ingredients; both exclude tri-state None (unlinked) per
            # ``matches_cookability``. One shared query (R-003).
            cookability = load_recipe_cookability(self.repository)
        expiring_counts: dict[UUID, int] | None = None
        if filters.expiring_within_days is not None:
            # C-waste W4 — narrow to recipes that use ≥1 in-stock ingredient
            # expiring within the horizon. Same predicate the rescue feed
            # uses (R-003); count cached on the handler so the hydration
            # step below doesn't recompute it.
            _, expiring_counts = count_expiring_ingredients_per_recipe(
                self.repository, filters.expiring_within_days,
            )
            self._expiring_counts = expiring_counts

        # Start with "every recipe id" as the candidate set, then narrow.
        # Loading every id is cheap enough to be honest at our scale.
        all_recipes = self.repository.get(Recipe).all()
        allowed: set[UUID] = {r.id for r in all_recipes}

        if filters.tags_include:
            allowed &= find_recipe_ids_with_all_tags(filters.tags_include)
        if filters.tags_exclude:
            allowed -= find_recipe_ids_with_any_tags(filters.tags_exclude)
        if filters.tools_include:
            allowed &= find_recipe_ids_with_all_tools(filters.tools_include)
        if filters.tools_exclude:
            allowed -= find_recipe_ids_with_any_tools(filters.tools_exclude)
        if filters.ingredient_exclude:
            allowed -= self._ingredient_excluded_recipe_ids(filters.ingredient_exclude)

        if cookability is not None and allowed:
            _kept: set[UUID] = set()
            for rid in allowed:
                missing, _ingr_count, unlinked = cookability.get(rid, (0, 0, 0))
                if filters.matches_cookability(missing, unlinked):
                    _kept.add(rid)
            allowed = _kept

        if expiring_counts is not None and allowed:
            allowed &= set(expiring_counts.keys())

        if not allowed:
            return query, True
        query = query.where(EntityField(Recipe, "id").in_(list(allowed)))
        return query, False

    def _compute_estimated_cost(self, dto: RecipeDto) -> RecipeDto:
        """C-4 Chunk 9 / DEC-5 — server-side cost estimate. For each
        ingredient that has a linked product carrying a current offer,
        sum `quantity * (offer.price_now / product.size_value)` to get
        an estimate. Ingredients without a linked-product offer fall back to
        the stock item's price observations (FU-216 — the everyday substrate);
        those with neither aren't priced. The caller surfaces "based on N of M"
        so the user reads the number as an estimate, not a quote.

        Stays server-side (DEC-5 / R-003 — domain math owned by the
        server, never duplicated on the client). Only the detail path
        triggers this; lists stay cheap.

        FU-463 — built with the ORM `select()` (not raw `text()`) so
        SQLAlchemy adapts UUID bindings to whatever the column type uses
        on each engine. The original raw-SQL version silently never
        matched on SQLite because the string IDs in the IN clause didn't
        compare against the UUIDType column (see
        `project_sqlite_uuid_text_binding` memory + FU-171). Symptom was
        `estimated_cost=None` on every recipe on SQLite deployments,
        regardless of whether the ingredients had priced products.
        """
        import dataclasses
        from dora_api.features.recipes.recipe_cost import \
            estimate_cost_for_ingredients

        if not dto.ingredients:
            return dto

        # R-003 — pricing ladder lives in one place (recipe_cost.py), shared
        # with the FU-451 swap ranker. This method now just adapts the result
        # onto the DTO.
        est = estimate_cost_for_ingredients(self.repository, dto.ingredients)
        return dataclasses.replace(
            dto,
            estimated_cost=est.estimated_cost,
            estimated_cost_priced_count=est.priced_count,
            estimated_cost_total_count=est.total_count,
        )

    def _nutrition_mode(self) -> str:
        """The install's nutrition mode. The rollup runs only in complex (off /
        simple have no linked-food data, so the field stays NULL rather than
        reporting a hollow "0 of 8" — R-029); `kcal_per_serving` is filled in
        simple too, from the typed number.""" 
        from dora_api.features.app_settings.access import get_or_create_app_setting
        from dora_api.features.nutrition.sources import nutrition_mode

        return nutrition_mode(get_or_create_app_setting(self.repository))

    @staticmethod
    def _nutrition_dto(rollup) -> 'RecipeNutritionDto':  # noqa: ANN001
        return RecipeNutritionDto(
            basis=rollup.basis,
            servings=rollup.servings,
            kcal=rollup.kcal,
            protein_g=rollup.protein_g,
            carbs_g=rollup.carbs_g,
            fat_g=rollup.fat_g,
            counted_count=rollup.counted_count,
            total_count=rollup.total_count,
            uncounted=rollup.uncounted,
            is_reliable=rollup.is_reliable,
        )

    def _compute_nutrition(self, dto: RecipeDto, entity: Recipe) -> RecipeDto:
        """FU-635 chunk 6 — complex-mode per-serving nutrition (detail path).

        Server-side for the same reason the cost estimate is (R-003): the
        gram-conversion ladder and the coverage rule are domain math, and a
        second copy in the SPA is how the two drift apart.
        """
        import dataclasses
        from dora_api.domain.entities.app_setting import NUTRITION_MODE_COMPLEX
        from dora_api.features.nutrition.recipe_rollup import (
            effective_kcal_per_serving, rollup_recipe_nutrition,
        )

        mode = self._nutrition_mode()
        rollup = (
            rollup_recipe_nutrition(self.repository, entity)
            if mode == NUTRITION_MODE_COMPLEX else None
        )
        kcal, reliable = effective_kcal_per_serving(mode, dto.kcal, rollup)
        return dataclasses.replace(
            dto,
            nutrition=self._nutrition_dto(rollup) if rollup is not None else None,
            kcal_per_serving=kcal,
            kcal_is_reliable=reliable,
        )

    def _hydrate_nutrition(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """FU-637 — the same rollup for a whole page, in three queries total.

        Unlike `estimated_cost` (detail-only), nutrition is needed *on the
        list*: the cookbook card shows kcal/serving and the "≤ N kcal" filter
        judges on it, and a per-recipe fetch to render a card badge would be
        the N+1 that `test_recipes_query_count` exists to catch.
        """
        import dataclasses
        from dora_api.domain.entities.app_setting import NUTRITION_MODE_COMPLEX
        from dora_api.features.nutrition.recipe_rollup import (
            IngredientInput, RecipeNutritionInput, effective_kcal_per_serving,
            rollup_recipes_nutrition,
        )

        if not dtos:
            return dtos
        mode = self._nutrition_mode()
        if mode != NUTRITION_MODE_COMPLEX:
            # Simple mode still gets an effective figure — the typed number —
            # so the cookbook card and filter read one field in every mode.
            return [
                dataclasses.replace(
                    dto,
                    **dict(zip(
                        ("kcal_per_serving", "kcal_is_reliable"),
                        effective_kcal_per_serving(mode, dto.kcal, None),
                    )),
                )
                for dto in dtos
            ]

        inputs = [
            RecipeNutritionInput(
                recipe_id=dto.recipe_id,
                servings=dto.servings,
                ingredients=[
                    IngredientInput(
                        stock_item_id=ing.stock_item_id,
                        stock_item_name=ing.stock_item_name,
                        quantity=ing.quantity,
                        unit=ing.unit,
                        is_optional=ing.is_optional,
                    )
                    for ing in dto.ingredients
                ],
            )
            for dto in dtos
        ]
        rollups = rollup_recipes_nutrition(self.repository, inputs)

        def _with_nutrition(dto: RecipeDto) -> RecipeDto:
            rollup = rollups.get(dto.recipe_id)
            if rollup is None:
                return dto
            kcal, reliable = effective_kcal_per_serving(mode, dto.kcal, rollup)
            return dataclasses.replace(
                dto,
                nutrition=self._nutrition_dto(rollup),
                kcal_per_serving=kcal,
                kcal_is_reliable=reliable,
            )

        return [_with_nutrition(dto) for dto in dtos]

    def _hydrate_has_image(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """FU-090 — bulk-derive `has_image` from a single SQL pass that
        never touches the deferred image blob column. SQL `image IS NOT
        NULL` does the work; the wire shape ends up the same as before
        but the recipe-list query no longer loads megabytes of bytes
        per row just to set a boolean.

        Routes through the ORM-mapped `Recipe` (not raw `text()`) so the
        SQLAlchemy UUID type handles the BINARY(16)-on-SQLite id column;
        raw `text('... IN :ids')` bound with str-UUIDs silently returns
        zero rows there (blob != string), yielding `has_image=False`
        across the board.
        """
        if not dtos:
            return dtos
        import dataclasses
        from sqlalchemy import select
        from dora_api.app import db

        ids = [d.recipe_id for d in dtos]
        stmt = select(Recipe.id, Recipe.image.is_not(None)).where(Recipe.id.in_(ids))
        rows = db.session.execute(stmt).all()
        flag_by_id = {str(row[0]): bool(row[1]) for row in rows}
        return [
            dataclasses.replace(d, has_image=flag_by_id.get(str(d.recipe_id), False))
            for d in dtos
        ]

    def _hydrate_section_count(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """List endpoint only — one bulk query for the section-count
        badge on each recipe card. Detail endpoint loads the full
        `sections[]` instead."""
        if not dtos:
            return dtos
        import dataclasses
        counts = get_section_count_for_recipes([d.recipe_id for d in dtos])
        return [
            dataclasses.replace(d, section_count=counts.get(d.recipe_id, 0))
            for d in dtos
        ]

    def _hydrate_structured_steps_flag(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """List endpoint only — set `has_structured_steps` via one bulk
        existence query. Detail endpoint (handle_by_id) goes further and
        loads the full `steps[]` list."""
        if not dtos:
            return dtos
        import dataclasses
        ids = [d.recipe_id for d in dtos]
        with_steps = has_structured_steps_for_recipes(ids)
        return [
            dataclasses.replace(d, has_structured_steps=d.recipe_id in with_steps)
            for d in dtos
        ]

    def _hydrate_has_step_images(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """List endpoint only — set `has_step_images` via one bulk
        existence query. Detail endpoint hydrates the full metadata list."""
        if not dtos:
            return dtos
        import dataclasses
        ids = [d.recipe_id for d in dtos]
        with_images = has_step_images_for_recipes(ids)
        return [
            dataclasses.replace(d, has_step_images=d.recipe_id in with_images)
            for d in dtos
        ]

    def _hydrate_expiring_count(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """C-waste W4 — fill `expiring_ingredient_count` from the cache
        the filter step populated. Skipped (zeros all the way) when the
        filter wasn't asked for, so the cookbook's default load stays
        unchanged."""
        if not dtos or not self._expiring_counts:
            return dtos
        import dataclasses
        return [
            dataclasses.replace(
                d,
                expiring_ingredient_count=self._expiring_counts.get(d.recipe_id, 0),
            )
            for d in dtos
        ]

    def _hydrate_tags(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """After paginate returns, bulk-load dietary tag + tool ids and rebuild
        the DTOs with them populated. The DTO is frozen, so we replace rather
        than mutate."""
        if not dtos:
            return dtos
        import dataclasses

        ids = [d.recipe_id for d in dtos]
        tag_map = get_tag_ids_for_recipes(ids)
        tool_map = get_tool_ids_for_recipes(ids)
        return [
            dataclasses.replace(
                d,
                dietary_tag_ids=tag_map.get(d.recipe_id, []),
                tool_ids=tool_map.get(d.recipe_id, []),
            )
            for d in dtos
        ]

    def _hydrate_unallocated(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """Subtract the sum of future, un-consumed servings per recipe
        from `available_meals` to derive the unallocated pool. One
        GROUP BY query keeps this O(1) regardless of list size.

        FU-081 — switched from raw `text()` to ORM `select()` against
        the mapped table. The text-form bound stringified UUIDs against
        the `UUIDType` BLOB columns on SQLite (string-vs-BLOB never
        matches), which silently kept `committed_meals` at 0 whenever
        future entries existed. The ORM form lets SQLAlchemy apply the
        UUIDType bind-processor and is portable across SQLite + Postgres.
        Same row set now also stamps `is_planned` (FU-081 derivation)."""
        if not dtos:
            return dtos
        import dataclasses
        from datetime import timedelta

        from sqlalchemy import func, select

        from dora_api.app import db
        from dora_api.features.app_settings.clock import household_today

        # "Today" in the household timezone (C-2.K), consistent with the
        # meal-plan rules — not server-local.
        _Today = household_today(self.repository)
        _Ids = [d.recipe_id for d in dtos]

        _Mpe = db.metadata.tables["MealPlanEntry"]

        _Stmt = (
            select(_Mpe.c.recipe_id, func.sum(_Mpe.c.servings))
            .where(_Mpe.c.consumed_at.is_(None))
            .where(_Mpe.c.scheduled_for >= _Today)
            .where(_Mpe.c.recipe_id.in_(_Ids))
            .group_by(_Mpe.c.recipe_id)
        )
        _Rows = db.session.execute(_Stmt).all()

        # how often each recipe appears across *all* meal plans (the
        # "frequently planned" tray): a plain all-time entry count.
        _CountStmt = (
            select(_Mpe.c.recipe_id, func.count())
            .where(_Mpe.c.recipe_id.in_(_Ids))
            .group_by(_Mpe.c.recipe_id)
        )
        _CountRows = db.session.execute(_CountStmt).all()

        # UUIDType columns are 16-byte BLOBs in SQLite; text() reads bring them
        # back as bytes. Normalise to a stable str key.
        def _key(v) -> str:
            if isinstance(v, UUID):
                return str(v)
            if isinstance(v, bytes):
                return str(UUID(bytes=v))
            return str(v)
        _Committed = {_key(row[0]): int(row[1] or 0) for row in _Rows}
        _PlanCount = {_key(row[0]): int(row[1] or 0) for row in _CountRows}

        # "haven't had in a while": never made, or last made before the
        # household 21-day window. The server owns the threshold (R-003).
        _StaleCutoff = _Today - timedelta(days=21)

        def _stale(d: RecipeDto) -> bool:
            # R-021 — `last_made_on` is a date now; compare directly.
            return d.last_made_on is None or d.last_made_on < _StaleCutoff

        return [
            dataclasses.replace(
                d,
                committed_meals = _Committed.get(str(d.recipe_id), 0),
                unallocated_meals = max(d.available_meals - _Committed.get(str(d.recipe_id), 0), 0),
                plan_count = _PlanCount.get(str(d.recipe_id), 0),
                not_made_recently = _stale(d),
                # same query already filtered to future-unconsumed
                # entries; any presence in _Committed means at least one
                # such row exists.
                is_planned = _Committed.get(str(d.recipe_id), 0) > 0,
            )
            for d in dtos
        ]

    def handle(
        self,
        options,
        filters: RecipeFilters | None = None,
    ) -> Page[RecipeDto]:
        filters = filters or RecipeFilters()
        query = self._base_query()
        query, empty_result = self._restrict_query(query, filters)
        if empty_result:
            return Page(items=[], total=0, page=options.page, limit=options.limit)
        page = query.paginate(
            options, RecipeDto.from_entity, field_map=_FIELD_MAP
        )
        import dataclasses
        _Hydrated = self._hydrate_nutrition(self._hydrate_unallocated(
            self._hydrate_has_image(
                self._hydrate_section_count(
                    self._hydrate_structured_steps_flag(
                        self._hydrate_has_step_images(
                            self._hydrate_expiring_count(
                                self._hydrate_tags(page.items)
                            )
                        )
                    )
                )
            )
        ))
        return dataclasses.replace(page, items=_Hydrated)

    def handle_by_id(self, recipe_id: UUID) -> RecipeDto | None:
        entity = self._base_query().by_id(recipe_id)
        if entity is None:
            return None
        dto = RecipeDto.from_entity(entity)
        # the `/<recipe_id>` route has no `uuid:` converter, so
        # Flask hands us a `str`. `get_tag_ids_for_recipes` returns a
        # dict keyed by real UUIDs (SQLAlchemy coerces the IN clause but
        # the dict's keys come from the result rows). A Python `.get(str)`
        # against UUID keys always misses, which silently dropped every
        # tag + tool on the detail endpoint. Look up via the loaded
        # entity's id (always a UUID) so the keys match.
        tag_map = get_tag_ids_for_recipes([entity.id])
        tool_map = get_tool_ids_for_recipes([entity.id])
        step_rows = get_steps_for_recipe(recipe_id)
        step_dtos = [
            RecipeStepDto(
                step_id=row["id"],
                parent_step_id=row["parent_step_id"],
                sequence=row["sequence"],
                text=row["text"],
                hint=row["hint"],
                ingredient_ids=row["ingredient_ids"],
                tool_ids=row["tool_ids"],
                section_id=row.get("section_id"),
            )
            for row in step_rows
        ]
        section_rows = get_sections_for_recipe(recipe_id)
        section_dtos = [
            RecipeSectionDto(
                section_id=row["id"],
                sequence=row["sequence"],
                name=row["name"],
            )
            for row in section_rows
        ]
        # sibling versions for the Versions card. One small
        # query; skipped entirely when the recipe has no group id.
        sibling_dtos: list[RecipeVersionSiblingDto] = []
        if entity.version_group_id is not None:
            siblings = (
                self.repository
                .get(Recipe)
                .all(
                    EntityField(Recipe, Recipe.Fields.VERSION_GROUP_ID).eq(entity.version_group_id),
                )
            )
            sibling_dtos = [
                RecipeVersionSiblingDto(
                    recipe_id=sib.id,
                    name=sib.name,
                    last_made_on=sib.last_made_on,
                    available_meals=sib.available_meals or 0,
                )
                for sib in siblings
                if sib.id != recipe_id
            ]
            sibling_dtos.sort(key=lambda s: s.name.lower())
        step_image_rows = get_step_image_metadata_for_recipe(entity.id)
        step_image_dtos = [
            RecipeStepImageDto(
                image_id=row["id"],
                sequence=row["sequence"],
            )
            for row in step_image_rows
        ]
        import dataclasses
        _WithAssoc = dataclasses.replace(
            dto,
            # keys are UUIDs from the SQL result; use entity.id
            # (a real UUID) instead of the route-string `recipe_id`.
            dietary_tag_ids=tag_map.get(entity.id, []),
            tool_ids=tool_map.get(entity.id, []),
            steps=step_dtos,
            has_structured_steps=bool(step_dtos),
            version_siblings=sibling_dtos,
            sections=section_dtos,
            section_count=len(section_dtos),
            step_images=step_image_dtos,
            has_step_images=bool(step_image_dtos),
        )
        _Hydrated = self._hydrate_unallocated(
            self._hydrate_has_image([_WithAssoc])
        )[0]
        return self._compute_nutrition(self._compute_estimated_cost(_Hydrated), entity)


def _parse_bool(raw: str | None) -> bool | None:
    """Tri-state query-flag parse: 'true'/'1'/'yes' → True, 'false'/'0'/'no' →
    False, missing/blank → None (no constraint)."""
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return None


def _parse_recipe_filters(args) -> RecipeFilters:
    """Read repeated query params (e.g. `?tags_include=vegan&tags_include=gluten-free`)
    plus comma-separated forms (`?tags_include=vegan,gluten-free`). Both
    are honoured because the SPA's `URLSearchParams` setter style and the
    Dora tool's `keywords-style` arg both feel natural.

    Also reads the cookability axes: `?cookable=true|false` and
    `?max_missing=N` (non-negative int; invalid → ignored)."""
    def collect(key: str) -> tuple[str, ...]:
        raw_values = args.getlist(key)
        if not raw_values:
            return ()
        merged: list[str] = []
        for raw in raw_values:
            for part in raw.split(","):
                trimmed = part.strip()
                if trimmed:
                    merged.append(trimmed)
        return tuple(merged)

    max_missing: int | None = None
    raw_max = args.get("max_missing")
    if raw_max is not None and raw_max.strip():
        try:
            parsed = int(raw_max)
            max_missing = parsed if parsed >= 0 else None
        except ValueError:
            max_missing = None

    expiring_within_days: int | None = None
    raw_expiring = args.get("expiring_within_days")
    if raw_expiring is not None and raw_expiring.strip():
        try:
            parsed_e = int(raw_expiring)
            # Cap at 60 days — the same ceiling the rescue feed uses
            # (`_MAX_HORIZON_DAYS` in waste.py). Negative values are
            # treated as "no constraint".
            if 0 <= parsed_e <= 60:
                expiring_within_days = parsed_e
        except ValueError:
            expiring_within_days = None

    return RecipeFilters(
        tags_include=collect("tags_include"),
        tags_exclude=collect("tags_exclude"),
        tools_include=collect("tools_include"),
        tools_exclude=collect("tools_exclude"),
        ingredient_exclude=collect("ingredient_exclude"),
        cookable=_parse_bool(args.get("cookable")),
        max_missing=max_missing,
        expiring_within_days=expiring_within_days,
    )


# ── GET /api/recipes/<id> ───────────────────────────────────────────────
# Real detail endpoint added in C-4 Chunk 8: the previous SPA path —
# filtering the list endpoint by id — only returned the list-shape DTO
# (no `steps[]`, no `version_siblings[]`). Detail views need the fully
# hydrated DTO that `handle_by_id` builds; this is its first dedicated
# route. The old filter-by-id path on the list endpoint still works as
# the cookbook overview's primary call (cheap list shape is fine there).

@RECIPE_ROUTER.route("/<uuid:recipe_id>", methods=["GET"])
def get_recipe(recipe_id: UUID):
    handler = GetRecipesHandler(SqlAlchemyRepository())
    dto = handler.handle_by_id(recipe_id)
    if dto is None:
        from dora_api.domain.entities.recipe import Recipe as _Recipe
        return not_found(_Recipe.__name__, recipe_id)
    return ok(dto)


@RECIPE_ROUTER.route("")
def get_recipes():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Filters = _parse_recipe_filters(request.args)
    try:
        _Page = GetRecipesHandler(SqlAlchemyRepository()).handle(_Options, _Filters)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(
        f"Retrieved {len(_Page.items)} of {_Page.total} recipes "
        f"(tags_include={_Filters.tags_include}, "
        f"tags_exclude={_Filters.tags_exclude}, "
        f"ingredient_exclude={_Filters.ingredient_exclude}, "
        f"cookable={_Filters.cookable}, max_missing={_Filters.max_missing}, "
        f"expiring_within_days={_Filters.expiring_within_days})."
    )
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)


# ── GET /api/recipes/tags ───────────────────────────────────────────────
# The SPA pulls the dietary-tag vocabulary at runtime so the picker stays in
# sync with the DB. The disclaimer travels with the list so any client can
# show the "planning aid, not a safety guarantee" framing without hardcoding
# the wording. The dedicated CRUD endpoints (/api/dietary-tags) own editing;
# this read stays here as the recipe-facing catalogue.

# ── GET /api/recipes/<id>/image ─────────────────────────────────────────
# Images are stored as a data-URL string (UTF-8 bytes) on the recipe row and
# served here as raw bytes so the SPA can use a plain <img src> without
# inlining megabytes of base64 into every list/detail JSON payload.

@RECIPE_ROUTER.route("/<uuid:recipe_id>/image", methods=["GET"])
def get_recipe_image(recipe_id):
    import base64
    import re as _re
    from flask import Response

    repository = SqlAlchemyRepository()
    recipe = repository.get(Recipe).by_id(recipe_id)
    if recipe is None or not recipe.image:
        return not_found(Recipe.__name__, recipe_id)
    data_url = recipe.image.decode("utf-8", "ignore")
    match = _re.match(r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$", data_url, _re.DOTALL)
    if not match:
        return not_found(Recipe.__name__, recipe_id)
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, TypeError):
        return not_found(Recipe.__name__, recipe_id)
    return Response(
        raw,
        mimetype=match.group("mime"),
        headers={"Cache-Control": "no-cache"},
    )


# ── GET /api/recipes/<id>/step-images/<image_id> ────────────────────────
# PROPOSAL_RECIPE_IMAGE_STEPS — step images are stored as data-URL bytes on
# the RecipeStepImage row and served here as raw bytes so the SPA can use a
# plain <img src>. Mirrors `/recipes/<id>/image` exactly; lives on a child
# route so the decoder stays a one-liner.

@RECIPE_ROUTER.route("/<uuid:recipe_id>/step-images/<uuid:image_id>", methods=["GET"])
def get_recipe_step_image(recipe_id, image_id):
    import base64
    import re as _re
    from flask import Response

    raw_bytes = get_step_image_bytes(UUID(str(recipe_id)), UUID(str(image_id)))
    if not raw_bytes:
        return not_found("RecipeStepImage", image_id)
    data_url = raw_bytes.decode("utf-8", "ignore")
    match = _re.match(
        r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$",
        data_url, _re.DOTALL,
    )
    if not match:
        return not_found("RecipeStepImage", image_id)
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, TypeError):
        return not_found("RecipeStepImage", image_id)
    return Response(
        raw,
        mimetype=match.group("mime"),
        headers={"Cache-Control": "no-cache"},
    )


@RECIPE_ROUTER.route("/tags", methods=["GET"])
def get_recipe_tag_catalogue():
    repository = SqlAlchemyRepository()
    tags = sorted(
        repository.get(DietaryTag).all(),
        key=lambda t: (t.sequence, t.name.lower()),
    )
    return ok({
        "tags": [
            {"value": str(t.id), "label": t.name, "category": t.category}
            for t in tags
        ],
        "disclaimer": RECIPE_TAG_DISCLAIMER,
    })
