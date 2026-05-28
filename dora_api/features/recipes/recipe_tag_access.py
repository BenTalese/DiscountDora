"""P2-08 — read/write helpers for the `RecipeTag` association table.

The table is a pure (recipe_id, tag) link without a standalone entity,
matching the StockItemSubstitute / StockItemProduct pattern. Handlers
access it via `db.metadata.tables["RecipeTag"]`; we centralise the
queries here so create/update/get can share one implementation and
ingest validation stays in one place.

All write helpers expect tags to be pre-validated against
`ALLOWED_RECIPE_TAGS` (in `dora_api/domain/recipe_tags.py`). Invalid
tags raise `ValueError`; the request layer catches it and returns a
422 with the bad value.
"""
from collections import defaultdict
from typing import Iterable
from uuid import UUID

from sqlalchemy import func, select

from dora_api.app import db
from dora_api.domain.recipe_tags import ALLOWED_RECIPE_TAGS


def _table():
    return db.metadata.tables["RecipeTag"]


def _normalise(tag: str) -> str:
    """Lowercase + strip — defensive against client mis-casing. Real
    validation against the curated catalogue happens in `validate_tags`."""
    return tag.strip().lower()


def validate_tags(tags: Iterable[str]) -> list[str]:
    """Return a deduped list of canonical tags. Raises ValueError on the
    first tag not in the curated catalogue so the caller can surface a
    precise error message."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in tags:
        canonical = _normalise(raw)
        if canonical not in ALLOWED_RECIPE_TAGS:
            raise ValueError(
                f"'{raw}' is not a recognised recipe tag. "
                f"See /api/recipes/tags for the canonical list."
            )
        if canonical in seen:
            continue
        seen.add(canonical)
        out.append(canonical)
    return out


def get_tags_for_recipe(recipe_id: UUID) -> list[str]:
    """Single-recipe load. For pages that render N recipes, prefer
    `get_tags_for_recipes` to avoid N round-trips."""
    table = _table()
    rows = db.session.execute(
        select(table.c.tag).where(table.c.recipe_id == recipe_id).order_by(table.c.tag)
    ).all()
    return [row[0] for row in rows]


def get_tags_for_recipes(recipe_ids: Iterable[UUID]) -> dict[UUID, list[str]]:
    """Bulk fetch — returns {recipe_id: [tag, ...]}. Missing keys mean
    the recipe has no tags (not an error). Sorted alphabetically for a
    stable order in the SPA chip row."""
    ids = list(recipe_ids)
    if not ids:
        return {}
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id, table.c.tag)
        .where(table.c.recipe_id.in_(ids))
        .order_by(table.c.recipe_id, table.c.tag)
    ).all()
    bucketed: dict[UUID, list[str]] = defaultdict(list)
    for recipe_id, tag in rows:
        bucketed[recipe_id].append(tag)
    return dict(bucketed)


def set_tags_for_recipe(recipe_id: UUID, tags: Iterable[str]) -> None:
    """Replace the tag set for a recipe. Idempotent — calling with the
    same set is a no-op. Validates against the curated catalogue;
    caller is responsible for catching ValueError.
    """
    canonical = validate_tags(tags)
    table = _table()
    db.session.execute(table.delete().where(table.c.recipe_id == recipe_id))
    if canonical:
        db.session.execute(
            table.insert(),
            [{"recipe_id": recipe_id, "tag": tag} for tag in canonical],
        )


def find_recipe_ids_with_all_tags(tags: Iterable[str]) -> set[UUID]:
    """Recipes that carry *every* tag in the input set. Used by the
    `tags_include` filter — semantics are "intersection", not "union",
    because the user's intent on a multi-select is "fits all of these"."""
    canonical = list({_normalise(t) for t in tags})
    if not canonical:
        return set()
    table = _table()
    # group-by + having-count is the canonical SQL for "must have all of".
    rows = db.session.execute(
        select(table.c.recipe_id)
        .where(table.c.tag.in_(canonical))
        .group_by(table.c.recipe_id)
        .having(func.count(table.c.tag.distinct()) == len(canonical))
    ).all()
    return {row[0] for row in rows}


def find_recipe_ids_with_any_tags(tags: Iterable[str]) -> set[UUID]:
    """Recipes that carry at least one of the tags. Used by
    `tags_exclude` — we exclude any recipe matching ANY of the
    exclusion tags (semantics: "none of these")."""
    canonical = list({_normalise(t) for t in tags})
    if not canonical:
        return set()
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id.distinct()).where(table.c.tag.in_(canonical))
    ).all()
    return {row[0] for row in rows}
