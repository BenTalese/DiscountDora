"""Canonical ordering for undirected stock-item substitute pairs.

The schema stores pairs with (a < b) so each unordered pair has one row.
Every read or write goes through `canonical_pair()` to keep the rest of
the code obvious — no caller has to reason about which item is "first".
"""
from uuid import UUID


def canonical_pair(x: UUID, y: UUID) -> tuple[UUID, UUID]:
    """Return (a, b) with a < b. Raises ValueError if x == y; callers
    that allow self-substitutes don't exist (and shouldn't)."""
    if x == y:
        raise ValueError("substitute pair cannot reference the same stock item")
    return (x, y) if str(x) < str(y) else (y, x)
