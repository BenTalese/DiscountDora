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
    ingredient list is cookable."""
    return missing_count_for(ingredients) == 0


def missing_stock_item_names_for(ingredients) -> list[str]:
    """Distinct names of the missing **required** stock items, alphabetised.

    Built off the already-loaded ingredient tree — never re-queries — so the
    recipe-list endpoint can surface "what's missing?" without an N+1. Sorted
    for deterministic output (client list rendering + test stability). Optional
    ingredients are excluded (§1.9).
    """
    seen: dict[str, None] = {}
    for ingredient in _required(ingredients):
        item = getattr(ingredient, "stock_item", None)
        if item is None or not is_missing(item.stock_level):
            continue
        seen.setdefault(item.name, None)
    return sorted(seen)
