"""Unit tests for the canonical stock-status contract.

The contract is the single source of truth for what a stock level *means*. These
tests pin its defining property: status is keyed to the level's ordinal
``sequence``, never its display name — so renaming a level in the UI cannot
change behaviour anywhere downstream (dashboard counts, alerts, cookability).
"""
from dataclasses import dataclass

from dora_api.domain.stock_status import (LOW_STOCK_SEQUENCE,
                                          OUT_OF_STOCK_SEQUENCE, StockStatus,
                                          is_low_stock, is_missing,
                                          is_out_of_stock, level_for_status,
                                          needs_restock, status_for)


@dataclass
class _Level:
    """Minimal stand-in for a StockLevel — only `sequence` and `name` matter."""
    sequence: int
    name: str = "irrelevant"


WELL = _Level(0, "Well-Stocked")
SUFFICIENT = _Level(1, "Sufficient Stock")
LOW = _Level(2, "Low Stock")
OUT = _Level(3, "Out of Stock")


def test__status_for__maps_each_sequence_to_its_role():
    assert status_for(WELL) is StockStatus.WELL_STOCKED
    assert status_for(SUFFICIENT) is StockStatus.SUFFICIENT_STOCK
    assert status_for(LOW) is StockStatus.LOW_STOCK
    assert status_for(OUT) is StockStatus.OUT_OF_STOCK
    assert status_for(None) is None


def test__status_is_keyed_to_sequence_not_name():
    # A level renamed to something unrecognisable still reads as out-of-stock
    # purely from its sequence — this is the whole point of the contract.
    renamed_out = _Level(OUT_OF_STOCK_SEQUENCE, name="Totally Different Label")
    assert is_out_of_stock(renamed_out) is True
    assert status_for(renamed_out) is StockStatus.OUT_OF_STOCK

    renamed_low = _Level(LOW_STOCK_SEQUENCE, name="zzz")
    assert is_low_stock(renamed_low) is True


def test__is_out_of_stock():
    assert is_out_of_stock(OUT) is True
    assert is_out_of_stock(LOW) is False
    assert is_out_of_stock(WELL) is False
    assert is_out_of_stock(None) is False


def test__is_low_stock_is_exact_band():
    assert is_low_stock(LOW) is True
    assert is_low_stock(OUT) is False  # out-of-stock is not "low"
    assert is_low_stock(SUFFICIENT) is False


def test__needs_restock_covers_low_and_out():
    assert needs_restock(LOW) is True
    assert needs_restock(OUT) is True
    assert needs_restock(SUFFICIENT) is False
    assert needs_restock(WELL) is False
    assert needs_restock(None) is False


def test__is_missing_is_out_of_stock_only_with_none_missing():
    # Decision (Chunk 1): missing = out-of-stock only; a None level counts missing.
    assert is_missing(OUT) is True
    assert is_missing(None) is True
    assert is_missing(LOW) is False
    assert is_missing(WELL) is False


def test__out_of_range_sequence_clamps_to_out_of_stock():
    beyond = _Level(99)
    assert status_for(beyond) is StockStatus.OUT_OF_STOCK
    assert is_out_of_stock(beyond) is True


def test__level_for_status_picks_by_sequence_ignoring_name():
    levels = [WELL, SUFFICIENT, LOW, OUT]
    assert level_for_status(levels, StockStatus.OUT_OF_STOCK) is OUT
    assert level_for_status(levels, StockStatus.WELL_STOCKED) is WELL
    # Missing role -> None, not an exception.
    assert level_for_status([WELL, LOW], StockStatus.SUFFICIENT_STOCK) is None
