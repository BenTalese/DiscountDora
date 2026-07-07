"""C-4 Chunk 8 — `POST /recipes/<id>/new-version`.

Per DEC-2 the version model is *flat*: recipes sharing a
`version_group_id` are equal peers (no current pointer, no snapshot vs
current distinction). New-version copies the source recipe (ingredients,
tools, steps, vocabulary, image, source URL) into a fresh row with the
same group id — and if the source had no group id yet, allocates one and
back-fills the source so the two recipes form the group.

The handler returns the new recipe id; the SPA routes into its detail
page with `(v<N>)` already in the name.

Allocations stay per-recipe (user picks which version they want when
scheduling a meal-plan entry); no version-aware allocation logic.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.types import EMPTY_UUID
from dora_api.features.recipes.recipe_step_access import (
    StepWrite, get_steps_for_recipe, replace_steps_for_recipe,
)
from dora_api.features.recipes.recipe_step_image_access import (
    StepImageWrite, get_step_image_metadata_for_recipe, get_step_image_bytes,
    replace_step_images_for_recipe,
)
from dora_api.features.recipes.recipe_tag_access import (
    get_tag_ids_for_recipe, set_tag_ids_for_recipe,
)
from dora_api.features.recipes.recipe_tool_access import (
    get_tool_ids_for_recipe, set_tool_ids_for_recipe,
)
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import created, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class NewRecipeVersionResponse:
    new_recipe_id: UUID = EMPTY_UUID
    source_not_found: bool = False


class NewRecipeVersionHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, source_id: UUID) -> NewRecipeVersionResponse:
        source: Recipe | None = (
            self.repository
            .get(Recipe)
            .include(Recipe.Fields.INGREDIENTS)
            # cuisine + category are noload now; the clone below
            # reads both off `source`, so eager-load them.
            .include(Recipe.Fields.CUISINE)
            .include(Recipe.Fields.CATEGORY)
            .one(EntityField(Recipe, "id").eq(source_id))
        )
        if source is None:
            return NewRecipeVersionResponse(source_not_found=True)

        # Resolve the group id. A singleton source gets a fresh group id
        # which is back-filled onto the source itself so the two recipes
        # form the group — otherwise the link would only exist on the new
        # row and we'd lose the symmetry the "equal peers" model expects.
        group_id = source.version_group_id
        if group_id is None:
            group_id = uuid4()
            source.version_group_id = group_id

        sibling_count = self._sibling_count(group_id)
        copy_name = f"{source.name} (v{sibling_count + 1})"

        # Clone ingredients first — the new recipe + its step links need
        # them inserted before the recipe save, so build them, add() each
        # (the repo assigns ids), and remember the old→new id map for
        # step linkage below.
        old_to_new_ing: dict[UUID, UUID] = {}
        cloned_ingredients: list[RecipeIngredient] = []
        for ing in (source.ingredients or []):
            cloned = RecipeIngredient(
                notes=ing.notes,
                quantity=ing.quantity,
                stock_item=ing.stock_item,
                unit=ing.unit,
            )
            cloned_ingredients.append(cloned)
        for ing in cloned_ingredients:
            self.repository.add(ing)
        for original, copy in zip(source.ingredients or [], cloned_ingredients):
            old_to_new_ing[original.id] = copy.id

        new_recipe = Recipe(
            available_meals=0,
            category=source.category,
            cook_time_minutes=source.cook_time_minutes,
            cuisine=source.cuisine,
            difficulty=source.difficulty,
            image=source.image,
            ingredients=cloned_ingredients,
            instructions=source.instructions,
            is_favourite=False,
            last_made_on=None,
            name=copy_name,
            prep_time_minutes=source.prep_time_minutes,
            recipe_collection=source.recipe_collection,
            servings=source.servings,
            source=source.source,
            time_of_day=source.time_of_day,
            version_group_id=group_id,
            kcal=source.kcal,
            steps_mode=source.steps_mode,
            # a new version is a fresh row in the household; stamp
            # at write time rather than carrying the source's created_at,
            # so the "Recently added" axis surfaces the version when it
            # was actually added here.
            created_at=datetime.now(timezone.utc),
        )
        self.repository.add(new_recipe)
        self.repository.save_changes()

        # Tags + tools — separate access helpers; safe to call after save.
        tag_ids = get_tag_ids_for_recipe(source_id)
        if tag_ids:
            set_tag_ids_for_recipe(new_recipe.id, tag_ids)
        tool_ids = get_tool_ids_for_recipe(source_id)
        if tool_ids:
            set_tool_ids_for_recipe(new_recipe.id, tool_ids)

        # Steps — map each step's `ingredient_ids` through the old→new
        # ingredient id map so the copies reference the *new* recipe's
        # ingredients rather than the source's. Step ids themselves get
        # fresh uuid4()s inside `replace_steps_for_recipe` via client_ids.
        source_steps = get_steps_for_recipe(source_id)
        if source_steps:
            old_step_id_to_client: dict[UUID, str] = {
                row["id"]: str(row["id"]) for row in source_steps
            }
            step_writes: list[StepWrite] = []
            for row in source_steps:
                parent = row["parent_step_id"]
                step_writes.append(StepWrite(
                    client_id=old_step_id_to_client[row["id"]],
                    parent_client_id=(
                        old_step_id_to_client[parent] if parent is not None else None
                    ),
                    sequence=row["sequence"],
                    text=row["text"],
                    hint=row["hint"],
                    ingredient_ids=[
                        old_to_new_ing[oid]
                        for oid in row["ingredient_ids"]
                        if oid in old_to_new_ing
                    ],
                    tool_ids=list(row["tool_ids"]),
                ))
            replace_steps_for_recipe(new_recipe.id, step_writes)

        # PROPOSAL_RECIPE_IMAGE_STEPS — clone ordered step images too. We
        # decode each row's bytes back into the data-URL string and feed
        # the access helper's write path so encoding stays consistent
        # across upload sites.
        source_images = get_step_image_metadata_for_recipe(source_id)
        if source_images:
            image_writes: list[StepImageWrite] = []
            for row in source_images:
                raw = get_step_image_bytes(source_id, row["id"])
                if raw is None:
                    continue
                image_writes.append(StepImageWrite(
                    sequence=row["sequence"],
                    image_data_url=raw.decode("utf-8", "ignore"),
                ))
            if image_writes:
                replace_step_images_for_recipe(new_recipe.id, image_writes)

        self.repository.save_changes()
        return NewRecipeVersionResponse(new_recipe_id=new_recipe.id)

    def _sibling_count(self, group_id: UUID) -> int:
        table = db.metadata.tables["Recipe"]
        rows = db.session.execute(
            select(table.c.id).where(table.c.version_group_id == group_id)
        ).all()
        return len(rows)


@RECIPE_ROUTER.route("<recipe_id>/new-version", methods=["POST"])
def new_recipe_version(recipe_id: UUID):
    logger = logging.getLogger(__name__)
    handler = get_container().inject(NewRecipeVersionHandler)
    response = handler.handle(recipe_id)
    if response.source_not_found:
        logger.warning(f"New version requested for missing recipe {recipe_id}.")
        return not_found(Recipe.__name__, recipe_id)
    from dora_api.features.recipes.get_recipes import (
        GetRecipesHandler, get_recipes,
    )
    dto = get_container().inject(GetRecipesHandler).handle_by_id(response.new_recipe_id)
    return created(
        response.new_recipe_id,
        f"{RECIPE_ROUTER.name}.{get_recipes.__name__}",
        "recipe_id",
        body=dto,
    )
