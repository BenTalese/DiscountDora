"""Recipe cookability — the single server-side authority for "can I cook this?".

Built on the stock-status contract (:func:`is_missing`). One ingredient listed on
multiple rows is still one shopping line, so "missing" is counted over *distinct*
stock items. This is the only place the aggregation rule lives — the recipe DTO,
the ``?cookable`` query filter, and the dashboard's ``cookable_count`` all consume
it so the definition can't drift (R-003).

Cookbook revision §1.9 — **optional ingredients are ignored entirely** by every
function in this module. A recipe with three missing optional items is still
cookable; the missing-name list and missing count both exclude optional rows.
There is no `cookable_with_optional` half-state.

IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — cookability is now **tri-state**: True /
False / None. ``None`` fires when any required ingredient is *unlinked*
(``stock_item_id IS NULL``) — the app admits "I don't know" instead of
fabricating True or False. Charter P3 Honest. R-010 closed-set. The plain
:func:`is_cookable` predicate that pre-dates this chunk still returns bool;
new code should call :func:`cookability_state` for the tri-state answer.
"""
from __future__ import annotations

from dora_api.domain.stock_status import is_missing


def _required(ingredients):
    """Filter out optional ingredients. Duck-typed: rows without an
    ``is_optional`` attribute (older fixtures / partial mocks) are treated as
    required, matching the column's NOT NULL default of false.
    """
    return [
        ingredient
        for ingredient in (ingredients or [])
        if not getattr(ingredient, "is_optional", False)
    ]


def unlinked_count_for(ingredients) -> int:
    """Number of *required* ingredients whose ``stock_item`` is None
    (unlinked). Optional rows are excluded — an unlinked optional
    ingredient doesn't gate cookability the way an unlinked required
    one does.
    """
    return sum(
        1 for ingredient in _required(ingredients)
        if getattr(ingredient, "stock_item", None) is None
    )


def missing_count_for(ingredients) -> int:
    """Number of *distinct* stock items in ``ingredients`` that count as missing.

    Duck-typed over recipe-ingredient entities: each must expose ``stock_item``
    (with ``id`` + ``stock_level``). Ingredients without a stock item are ignored
    (they can't reference a pantry item to be missing). Optional ingredients are
    ignored entirely (§1.9).
    """
    return len({
        ingredient.stock_item.id
        for ingredient in _required(ingredients)
        if ingredient.stock_item is not None
        and is_missing(ingredient.stock_item.stock_level)
    })


def is_cookable(ingredients) -> bool:
    """True when nothing required is missing. An empty (or all-optional)
    ingredient list is cookable.

    NOTE: this is the pre-Chunk-4 boolean predicate — it treats unlinked
    required ingredients as "not missing" (no stock_item ⇒ no stock level
    ⇒ can't be missing). New code should call :func:`cookability_state`
    which returns ``None`` when any required ingredient is unlinked, so
    the honest "unknown" state propagates through the DTO / filter chain.
    """
    return missing_count_for(ingredients) == 0


def cookability_state(ingredients) -> bool | None:
    """Tri-state cookability: True / False / None.

    * ``None`` — at least one *required* ingredient is unlinked
      (``stock_item is None``). The app can't answer "can I cook this?"
      without knowing what item to check the stock level of. P3 Honest.
    * ``True`` — every required ingredient links to a StockItem, none of
      which are missing. An empty (or all-optional) ingredient list is
      cookable (same as :func:`is_cookable`).
    * ``False`` — every required ingredient links to a StockItem, and at
      least one is missing.
    """
    if unlinked_count_for(ingredients) > 0:
        return None
    return missing_count_for(ingredients) == 0


def missing_stock_item_names_for(ingredients) -> list[str]:
    """Distinct names of the missing **required** stock items, alphabetised.

    Built off the already-loaded ingredient tree — never re-queries — so the
    recipe-list endpoint can surface "what's missing?" without an N+1. Sorted
    for deterministic output (client list rendering + test stability). Optional
    ingredients are excluded (§1.9). Unlinked ingredients contribute nothing
    to this list — the caller reads ``cookability_state()`` to know when
    "missing" is meaningful.
    """
    seen: dict[str, None] = {}
    for ingredient in _required(ingredients):
        item = getattr(ingredient, "stock_item", None)
        if item is None or not is_missing(item.stock_level):
            continue
        seen.setdefault(item.name, None)
    return sorted(seen)
