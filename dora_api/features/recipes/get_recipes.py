import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from flask import request

from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.recipe_tags import (RECIPE_TAG_CATALOGUE,
                                         RECIPE_TAG_DISCLAIMER)
from dora_api.features.recipes.recipe_tag_access import (
    find_recipe_ids_with_all_tags, find_recipe_ids_with_any_tags,
    get_tags_for_recipes,
)
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class RecipeIngredientDto:
    recipe_ingredient_id: UUID
    stock_item_id: UUID
    stock_item_name: str
    stock_level_id: UUID | None
    # Direct location only — the frontend resolves the full breadcrumb via
    # the cached locations tree so recipe queries stay cheap.
    stock_location_id: UUID | None
    stock_location_name: str | None
    quantity: float | None
    unit: str | None
    notes: str | None

    @classmethod
    def from_entity(cls, ingredient: RecipeIngredient) -> 'RecipeIngredientDto':
        _Item = ingredient.stock_item
        _Loc = _Item.stock_location if _Item else None
        return RecipeIngredientDto(
            recipe_ingredient_id = ingredient.id,
            stock_item_id = _Item.id,
            stock_item_name = _Item.name,
            stock_level_id = _Item.stock_level.id if _Item.stock_level else None,
            stock_location_id = _Loc.id if _Loc else None,
            stock_location_name = _Loc.name if _Loc else None,
            quantity = ingredient.quantity,
            unit = ingredient.unit,
            notes = ingredient.notes,
        )


@dataclass(frozen=True, slots=True)
class RecipeDto:
    recipe_id: UUID
    name: str
    category: str | None
    cook_time_minutes: int | None
    cuisine: str | None
    difficulty: str | None
    instructions: str | None
    is_favourite: bool
    last_made_on: datetime | None
    nutrition: str | None
    prep_time_minutes: int | None
    recipe_collection_id: UUID | None
    servings: int | None
    time_of_day: str | None
    ingredients: List[RecipeIngredientDto]
    # P2-08 — canonical dietary / allergen-free / nutritional tags. Empty
    # list when the recipe has none. Set by the handler after the base
    # query — the field is mutable to keep `from_entity` agnostic of
    # tag loading.
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_entity(cls, recipe: Recipe, tags: list[str] | None = None) -> 'RecipeDto':
        return RecipeDto(
            recipe_id = recipe.id,
            name = recipe.name,
            category = recipe.category,
            cook_time_minutes = recipe.cook_time_minutes,
            cuisine = recipe.cuisine,
            difficulty = recipe.difficulty,
            instructions = recipe.instructions,
            is_favourite = recipe.is_favourite,
            last_made_on = recipe.last_made_on,
            nutrition = recipe.nutrition,
            prep_time_minutes = recipe.prep_time_minutes,
            recipe_collection_id = recipe.recipe_collection.id if recipe.recipe_collection else None,
            servings = recipe.servings,
            time_of_day = recipe.time_of_day,
            ingredients = [RecipeIngredientDto.from_entity(i) for i in (recipe.ingredients or [])],
            tags = tags or [],
        )


_FIELD_MAP: dict[str, EntityField] = {
    "recipe_id": EntityField(Recipe, "id"),
    "recipe_collection_id": EntityField(Recipe, "_recipe_collection_id"),
}


@dataclass(frozen=True, slots=True)
class RecipeTagFilters:
    """P2-08 — three independent recipe filters that compose with AND.

    - tags_include : recipe must carry every tag in this list.
    - tags_exclude : recipe must carry none of the tags in this list.
    - ingredient_exclude : recipe must not have an ingredient whose stock
      item name contains any of the substrings (case-insensitive). Lets
      users say "free from egg" without us having to maintain an allergen
      taxonomy.
    """
    tags_include: tuple[str, ...] = ()
    tags_exclude: tuple[str, ...] = ()
    ingredient_exclude: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (self.tags_include or self.tags_exclude or self.ingredient_exclude)


class GetRecipesHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

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

    def _restrict_query(self, query, filters: RecipeTagFilters):
        """Resolve the three filter axes into a single `id IN (...)`
        constraint applied to the page query. Returns the (possibly
        unchanged) query plus a boolean that's True when the filter set
        guarantees an empty result (e.g. `tags_include` matched zero
        recipes), so the caller can short-circuit the paginate."""
        if filters.is_empty:
            return query, False

        # Start with "every recipe id" as the candidate set, then narrow.
        # Loading every id is cheap enough to be honest at our scale.
        all_recipes = self.repository.get(Recipe).all()
        allowed: set[UUID] = {r.id for r in all_recipes}

        if filters.tags_include:
            allowed &= find_recipe_ids_with_all_tags(filters.tags_include)
        if filters.tags_exclude:
            allowed -= find_recipe_ids_with_any_tags(filters.tags_exclude)
        if filters.ingredient_exclude:
            allowed -= self._ingredient_excluded_recipe_ids(filters.ingredient_exclude)

        if not allowed:
            return query, True
        query = query.where(EntityField(Recipe, "id").in_(list(allowed)))
        return query, False

    def _hydrate_tags(self, dtos: list[RecipeDto]) -> list[RecipeDto]:
        """After paginate returns, bulk-load tags and rebuild the DTOs
        with them populated. The DTO is frozen, so we replace rather
        than mutate."""
        if not dtos:
            return dtos
        import dataclasses

        tag_map = get_tags_for_recipes([d.recipe_id for d in dtos])
        return [
            dataclasses.replace(d, tags=tag_map.get(d.recipe_id, []))
            for d in dtos
        ]

    def handle(
        self,
        options,
        filters: RecipeTagFilters | None = None,
    ) -> Page[RecipeDto]:
        filters = filters or RecipeTagFilters()
        query = self._base_query()
        query, empty_result = self._restrict_query(query, filters)
        if empty_result:
            return Page(items=[], total=0, page=options.page, limit=options.limit)
        page = query.paginate(
            options, RecipeDto.from_entity, field_map=_FIELD_MAP
        )
        import dataclasses
        return dataclasses.replace(page, items=self._hydrate_tags(page.items))

    def handle_by_id(self, recipe_id: UUID) -> RecipeDto | None:
        entity = self._base_query().by_id(recipe_id)
        if entity is None:
            return None
        dto = RecipeDto.from_entity(entity)
        tag_map = get_tags_for_recipes([recipe_id])
        import dataclasses
        return dataclasses.replace(dto, tags=tag_map.get(recipe_id, []))


def _parse_tag_filters(args) -> RecipeTagFilters:
    """Read repeated query params (e.g. `?tags_include=vegan&tags_include=gluten-free`)
    plus comma-separated forms (`?tags_include=vegan,gluten-free`). Both
    are honoured because the SPA's `URLSearchParams` setter style and the
    Dora tool's `keywords-style` arg both feel natural."""
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

    return RecipeTagFilters(
        tags_include=collect("tags_include"),
        tags_exclude=collect("tags_exclude"),
        ingredient_exclude=collect("ingredient_exclude"),
    )


@RECIPE_ROUTER.route("")
def get_recipes():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Filters = _parse_tag_filters(request.args)
    try:
        _Page = get_container().inject(GetRecipesHandler).handle(_Options, _Filters)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(
        f"Retrieved {len(_Page.items)} of {_Page.total} recipes "
        f"(tags_include={_Filters.tags_include}, "
        f"tags_exclude={_Filters.tags_exclude}, "
        f"ingredient_exclude={_Filters.ingredient_exclude})."
    )
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)


# ── GET /api/recipes/tags ───────────────────────────────────────────────
# The SPA pulls the curated tag list at runtime so the picker stays in
# sync with the backend constants. The disclaimer travels with the list
# so any client surfacing the picker can show the "planning aid, not a
# safety guarantee" framing without hardcoding the wording.

@RECIPE_ROUTER.route("/tags", methods=["GET"])
def get_recipe_tag_catalogue():
    return ok({
        "tags": [
            {"value": t.value, "label": t.label, "category": t.category}
            for t in RECIPE_TAG_CATALOGUE
        ],
        "disclaimer": RECIPE_TAG_DISCLAIMER,
    })
