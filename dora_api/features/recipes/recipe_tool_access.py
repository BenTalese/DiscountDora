"""C-4 Chunk 5 — read/write helpers for the `RecipeTool` association table.

Pure (recipe_id, tool_id) link with no standalone entity (matching
recipe_tag_access). Write helpers validate ids against existing Tool rows;
unknown ids raise ValueError → 400 at the request layer.
"""
from collections import defaultdict
from typing import Iterable
from uuid import UUID

from sqlalchemy import func, select

from dora_api.app import db


def _table():
    return db.metadata.tables["RecipeTool"]


def _tool_table():
    return db.metadata.tables["Tool"]


def _coerce_uuid(value) -> UUID | None:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _all_tool_ids() -> set[UUID]:
    tools = _tool_table()
    return {row[0] for row in db.session.execute(select(tools.c.id)).all()}


def _name_to_id() -> dict[str, UUID]:
    tools = _tool_table()
    rows = db.session.execute(select(tools.c.name, tools.c.id)).all()
    return {name.strip().lower(): tool_id for name, tool_id in rows}


def validate_tool_ids(tool_ids: Iterable) -> list[UUID]:
    """Return a deduped list of valid Tool ids; raise ValueError on the first
    unknown id."""
    known = _all_tool_ids()
    seen: set[UUID] = set()
    out: list[UUID] = []
    for raw in tool_ids:
        coerced = _coerce_uuid(raw)
        if coerced is None or coerced not in known:
            raise ValueError(
                f"'{raw}' is not a recognised tool. See /api/tools for the list."
            )
        if coerced in seen:
            continue
        seen.add(coerced)
        out.append(coerced)
    return out


def resolve_tool_filter_values(values: Iterable[str]) -> set[UUID]:
    """Map filter inputs (ids OR names) to ids, dropping unknowns silently."""
    known = _all_tool_ids()
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


def get_tool_ids_for_recipes(recipe_ids: Iterable[UUID]) -> dict[UUID, list[UUID]]:
    ids = list(recipe_ids)
    if not ids:
        return {}
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id, table.c.tool_id)
        .where(table.c.recipe_id.in_(ids))
        .order_by(table.c.recipe_id)
    ).all()
    bucketed: dict[UUID, list[UUID]] = defaultdict(list)
    for recipe_id, tool_id in rows:
        bucketed[recipe_id].append(tool_id)
    return dict(bucketed)


def get_tool_ids_for_recipe(recipe_id: UUID) -> list[UUID]:
    return get_tool_ids_for_recipes([recipe_id]).get(recipe_id, [])


def set_tool_ids_for_recipe(recipe_id: UUID, tool_ids: Iterable) -> None:
    """Replace the tool set for a recipe. Idempotent. Validates ids; caller
    catches ValueError."""
    valid = validate_tool_ids(tool_ids)
    table = _table()
    db.session.execute(table.delete().where(table.c.recipe_id == recipe_id))
    if valid:
        db.session.execute(
            table.insert(),
            [{"recipe_id": recipe_id, "tool_id": tool_id} for tool_id in valid],
        )


def find_recipe_ids_with_all_tools(tool_ids: Iterable) -> set[UUID]:
    wanted = list(resolve_tool_filter_values(tool_ids))
    if not wanted:
        return set()
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id)
        .where(table.c.tool_id.in_(wanted))
        .group_by(table.c.recipe_id)
        .having(func.count(table.c.tool_id.distinct()) == len(wanted))
    ).all()
    return {row[0] for row in rows}


def find_recipe_ids_with_any_tools(tool_ids: Iterable) -> set[UUID]:
    wanted = list(resolve_tool_filter_values(tool_ids))
    if not wanted:
        return set()
    table = _table()
    rows = db.session.execute(
        select(table.c.recipe_id.distinct()).where(table.c.tool_id.in_(wanted))
    ).all()
    return {row[0] for row in rows}


def _step_table():
    return db.metadata.tables["RecipeStep"]


def _step_tool_table():
    return db.metadata.tables["RecipeStepTool"]


def get_tool_ids_from_steps(recipe_id: UUID) -> list[UUID]:
    """The union of the tools every structured step of ``recipe_id`` declares,
    in first-appearance order (steps ordered by parent-then-sequence)."""
    steps = _step_table()
    step_tools = _step_tool_table()
    rows = db.session.execute(
        select(step_tools.c.tool_id)
        .select_from(steps.join(step_tools, step_tools.c.step_id == steps.c.id))
        .where(steps.c.recipe_id == recipe_id)
        .order_by(steps.c.parent_step_id, steps.c.sequence)
    ).all()
    seen: set[UUID] = set()
    out: list[UUID] = []
    for (tool_id,) in rows:
        if tool_id in seen:
            continue
        seen.add(tool_id)
        out.append(tool_id)
    return out


def sync_recipe_tools_from_steps(recipe_id: UUID) -> list[UUID]:
    """Recipe-view feedback 2026-08-27 — in ``structured`` mode a recipe's
    tools are *derived*, not typed: the recipe-level set is the union of what
    its steps say they use.

    The recipe-level `RecipeTool` rows still exist because that is what the
    cookbook's tool filter reads (`find_recipe_ids_with_any_tools`), and
    re-deriving it per query would push step-shaped domain math into the list
    endpoint. So the union is computed once, here, on every write that can
    change it, and the page shows it read-only.

    Freeform/image recipes have no steps to derive from and keep their own
    editable set — callers only reach this in structured mode. Returns the
    ids written, for the caller's DTO.
    """
    derived = get_tool_ids_from_steps(recipe_id)
    set_tool_ids_for_recipe(recipe_id, derived)
    return derived
