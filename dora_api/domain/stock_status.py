"""Canonical stock-status authority.

The single server-side source of truth for what a stock level *means*. Status is
keyed to the level's ordinal ``sequence``, **never** its display name — renaming a
level's label in the UI must not change behaviour. Every feature that buckets,
derives, or assigns stock status consumes this module; no other code may compare a
stock-level name or hardcode a bare sequence literal.

Seeded sequences (see ``persistence/seed.py`` / the initial migration):
0 Well-Stocked, 1 Sufficient Stock, 2 Low Stock, 3 Out of Stock.

"Missing" semantics (used for ingredient cookability): out-of-stock **only** — a
low-stock ingredient you can usually still cook with.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Iterable, Optional


class StockStatus(IntEnum):
    """Stock-level roles, ordered worst-last by ``sequence``."""
    WELL_STOCKED = 0
    SUFFICIENT_STOCK = 1
    LOW_STOCK = 2
    OUT_OF_STOCK = 3


# Readable aliases for the canonical sequence values. Prefer the predicates
# below to bare comparisons; these exist for the few ordinal cases.
WELL_STOCKED_SEQUENCE = int(StockStatus.WELL_STOCKED)
SUFFICIENT_STOCK_SEQUENCE = int(StockStatus.SUFFICIENT_STOCK)
LOW_STOCK_SEQUENCE = int(StockStatus.LOW_STOCK)
OUT_OF_STOCK_SEQUENCE = int(StockStatus.OUT_OF_STOCK)


def _sequence_of(level) -> Optional[int]:
    if level is None:
        return None
    return getattr(level, "sequence", None)


def status_for(level) -> Optional[StockStatus]:
    """The :class:`StockStatus` for a stock level, or ``None`` if unknown.

    A sequence at or beyond the worst defined value clamps to OUT_OF_STOCK so a
    future-inserted level never silently reads as "no status".
    """
    seq = _sequence_of(level)
    if seq is None:
        return None
    if seq >= OUT_OF_STOCK_SEQUENCE:
        return StockStatus.OUT_OF_STOCK
    try:
        return StockStatus(seq)
    except ValueError:
        return None


def is_out_of_stock(level) -> bool:
    seq = _sequence_of(level)
    return seq is not None and seq >= OUT_OF_STOCK_SEQUENCE


def is_low_stock(level) -> bool:
    """Exactly the Low-Stock band — not out-of-stock."""
    return _sequence_of(level) == LOW_STOCK_SEQUENCE


def needs_restock(level) -> bool:
    """At or below the low-stock threshold (low **or** out)."""
    seq = _sequence_of(level)
    return seq is not None and seq >= LOW_STOCK_SEQUENCE


def is_missing(level) -> bool:
    """Whether an ingredient counts as missing for cookability.

    A ``None`` level (no stock record) counts as missing; otherwise out-of-stock
    only — see the module "Missing semantics" note.
    """
    return level is None or is_out_of_stock(level)


def level_for_status(levels: Iterable, status: StockStatus):
    """Return the level in ``levels`` whose sequence matches ``status``, else ``None``.

    Pure: the caller owns the DB round-trip and passes the already-fetched levels.
    Use this instead of looking a level up by name to assign it.
    """
    target = int(status)
    for level in levels:
        if getattr(level, "sequence", None) == target:
            return level
    return None
