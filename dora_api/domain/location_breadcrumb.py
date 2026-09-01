"""Breadcrumb for a stock location — the one implementation.

R-003 (single source of truth). Four hand-rolled parent-chain walks had grown
up independently — stock-item detail, shopping-list detail, global search and
(as of the stocktake location fix) the stocktake session — each with its own
copy of the same loop and its own cycle guard. They agreed by luck; a fifth
copy is how they'd stop agreeing. Callers now supply the id→location lookup
they already had to build anyway, and get the same list back.
"""

from __future__ import annotations

from typing import List, Mapping
from uuid import UUID

from dora_api.domain.entities.stock_location import StockLocation

# A location tree deeper than this is a data bug (or a parent cycle), not a
# pantry. Bail rather than spin.
_MAX_DEPTH = 16


def build_breadcrumb(
    location: StockLocation | None,
    locations_by_id: Mapping[UUID, StockLocation],
) -> List[str]:
    """Root-first path of names — ``["Pantry", "Middle shelf", "Left side"]``.

    Returns ``[]`` for ``None`` so callers can fall back to their own
    placeholder without a second null check.
    """
    if location is None:
        return []
    path: List[str] = []
    cursor: StockLocation | None = location
    depth = _MAX_DEPTH
    while cursor is not None and depth > 0:
        path.append(cursor.name)
        cursor = locations_by_id.get(cursor.parent_id) if cursor.parent_id else None
        depth -= 1
    path.reverse()
    return path
