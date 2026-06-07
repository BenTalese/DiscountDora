"""Recipe cookability — the single server-side authority for "can I cook this?".

Built on the stock-status contract (:func:`is_missing`). One ingredient listed on
multiple rows is still one shopping line, so "missing" is counted over *distinct*
stock items. This is the only place the aggregation rule lives — the recipe DTO,
the ``?cookable`` query filter, and the dashboard's ``cookable_count`` all consume
it so the definition can't drift (R-003).
"""
from __future__ import annotations

from dora_api.domain.stock_status import is_missing


def missing_count_for(ingredients) -> int:
    """Number of *distinct* stock items in ``ingredients`` that count as missing.

    Duck-typed over recipe-ingredient entities: each must expose ``stock_item``
    (with ``id`` + ``stock_level``). Ingredients without a stock item are ignored
    (they can't reference a pantry item to be missing).
    """
    return len({
        ingredient.stock_item.id
        for ingredient in (ingredients or [])
        if ingredient.stock_item is not None
        and is_missing(ingredient.stock_item.stock_level)
    })


def is_cookable(ingredients) -> bool:
    """True when nothing is missing. An empty ingredient list is cookable."""
    return missing_count_for(ingredients) == 0
