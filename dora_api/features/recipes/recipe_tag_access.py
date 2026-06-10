"""C-4 Chunk 2 — read/write helpers for the `RecipeTag` association table.

The table is a pure (recipe_id, dietary_tag_id) link without a standalone
entity, matching the StockItemSubstitute / StockItemProduct pattern.
Handlers access it via `db.metadata.tables["RecipeTag"]`; we centralise the
queries here so create/update/get share one implementation and validation
stays in one place.

Tags are now the user-configurable `DietaryTag` vocabulary (was an in-code
catalogue). Write helpers validate ids against existing DietaryTag rows;
unknown ids raise `ValueError`, which the request layer turns into a 400.
"""
from collections import defaultdict
from typing import Iterable
from uuid import UUID

from sqlalchemy import func, select

from dora_api.app import db


def _table():
    return db.metadata.tables["RecipeTag"]


def _tag_table():
    return db.metadata.tables["DietaryTag"]


def _coerce_uuid(value) -> UUID | None:
    """Best-effort coercion to UUID; returns None on anything unparseable so
    filter paths can skip junk rather than 500."""
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _all_tag_ids() -> set[UUID]:
    tags = _tag_table()
    rows = db.session.execute(select(tags.c.id)).all()
    return {row[0] for row in rows}


def _name_to_id() -> dict[str, UUID]:
    tags = _tag_table()
    rows = db.session.execute(select(tags.c.name, tags.c.id)).all()
    return {name.strip().lower(): tag_id for name, tag_id in rows}


def validate_tag_ids(tag_ids: Iterable) -> list[UUID]:
    """Return a deduped list of valid DietaryTag ids. Raises ValueError on
    the first id that doesn't exist so the caller can surface a precise error."""
    known = _all_tag_ids()
    seen: set[UUID] = set()
    out: list[UUID] = []
    for raw in tag_ids:
        coerced = _coerce_uuid(raw)
        if coerced is None or coerced not in known:
            raise ValueError(
                f"'{raw}' is not a recognised dietary tag. "
                f"See /api/recipes/tags for the available list."
            )
        if coerced in seen:
            continue
        seen.add(coerced)
        out.append(coerced)
    return out


def resolve_tag_filter_values(values: Iterable[str]) -> set[UUID]:
    """Map filter inputs (tag ids OR human-friendly names) to ids, silently
    dropping anything that matches neither. Lets the SPA pass ids and Dora's
    tools pass names through the same filter path without erroring on a typo."""
    known = _all_tag_ids()
    by_name = _name_to_id()
    out: set[UUID] = set()
    for raw in values:
        coerced = _coerce_uuid(raw)
        if coerced is not None and coerced in known:
            out.add(coerced)
            continue
        named = by_name.get(str(raw).strip().lower())
        if named is not None:
            out.add(named)
    return out


def get_tag_ids_for_recipe(recipe_id: UUID) -> list[UUID]:
    """Single-recipe load. For pages rendering N recipes, prefer
    `get_tag_ids_for_recipes` to avoid N round-trips."""
    table = _table()
    rows = db.session.execute(
        select(table.c.dietary_tag_id).where(table.c.recipe_id == recipe_id)
    ).all()
    return [row[0] for row in rows]


def get_tag_ids_for_recipes(recipe_ids: Iterable[UUID]) -> dict[UUID, list[UUID]]:
    """Bulk fetch — returns {recipe_id: [dietary_tag_id, ...]}. Missing keys
    mean the recipe has no tags (not an error)."""
    ids = list(recipe_ids)
    if not ids:
        return {}
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id, table.c.dietary_tag_id)
        .where(table.c.recipe_id.in_(ids))
        .order_by(table.c.recipe_id)
    ).all()
    bucketed: dict[UUID, list[UUID]] = defaultdict(list)
    for recipe_id, tag_id in rows:
        bucketed[recipe_id].append(tag_id)
    return dict(bucketed)


def get_tag_names_for_recipes(recipe_ids: Iterable[UUID]) -> dict[UUID, list[str]]:
    """Bulk fetch of human-readable tag names per recipe — for surfaces that
    show names rather than ids (e.g. the assistant). {recipe_id: [name, ...]}."""
    ids = list(recipe_ids)
    if not ids:
        return {}
    table = _table()
    tags = _tag_table()
    rows = db.session.execute(
        select(table.c.recipe_id, tags.c.name)
        .select_from(table.join(tags, table.c.dietary_tag_id == tags.c.id))
        .where(table.c.recipe_id.in_(ids))
        .order_by(tags.c.name)
    ).all()
    bucketed: dict[UUID, list[str]] = defaultdict(list)
    for recipe_id, name in rows:
        bucketed[recipe_id].append(name)
    return dict(bucketed)


def set_tag_ids_for_recipe(recipe_id: UUID, tag_ids: Iterable) -> None:
    """Replace the tag set for a recipe. Idempotent. Validates each id exists;
    caller is responsible for catching ValueError."""
    valid = validate_tag_ids(tag_ids)
    table = _table()
    db.session.execute(table.delete().where(table.c.recipe_id == recipe_id))
    if valid:
        db.session.execute(
            table.insert(),
            [{"recipe_id": recipe_id, "dietary_tag_id": tag_id} for tag_id in valid],
        )


def find_recipe_ids_with_all_tags(tag_ids: Iterable) -> set[UUID]:
    """Recipes that carry *every* tag in the input set (intersection — the
    user's intent on a multi-select is "fits all of these")."""
    wanted = list(resolve_tag_filter_values(tag_ids))
    if not wanted:
        return set()
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id)
        .where(table.c.dietary_tag_id.in_(wanted))
        .group_by(table.c.recipe_id)
        .having(func.count(table.c.dietary_tag_id.distinct()) == len(wanted))
    ).all()
    return {row[0] for row in rows}


def find_recipe_ids_with_any_tags(tag_ids: Iterable) -> set[UUID]:
    """Recipes carrying at least one of the tags (union — used by the exclude
    axis: drop any recipe matching ANY exclusion tag)."""
    wanted = list(resolve_tag_filter_values(tag_ids))
    if not wanted:
        return set()
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id.distinct()).where(table.c.dietary_tag_id.in_(wanted))
    ).all()
    return {row[0] for row in rows}
