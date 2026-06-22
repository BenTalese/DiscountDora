"""Unit tests for server-owned shopping-list totals (state-ownership Type B).

These pin that `compute_list_totals` reproduces the browser's old
`primaryListStats` math (`priceOfLine` / `savingsOfLine` / `chosenOfferFor` in
`shoppingList.ts`) exactly — moving the cross-line SUM to the server must not
change the displayed numbers.
"""
from datetime import datetime
from uuid import uuid4

from dora_api.features.shopping_lists.get_shopping_list_detail import (
    LineProductOfferDto, ShoppingListLineDto, compute_list_totals)


def _offer(price_now, price_was, *, is_selected=False):
    return LineProductOfferDto(
        product_id=uuid4(), name="p", brand=None, store_id=uuid4(),
        store_name="m", size=None, price_now=price_now, price_was=price_was,
        is_selected=is_selected,
    )


def _line(*, quantity=1, is_ticked=False, actual_unit_price=None,
          selected_product_id=None, offers=()):
    return ShoppingListLineDto(
        # FU-136 — `product_id` became required on the DTO when Cart
        # Button Chunk 3 added the standalone-product anchor. These
        # tests exercise totals only, so product_id is irrelevant —
        # pass None and keep the test stub current.
        line_id=uuid4(), stock_item_id=uuid4(), product_id=None,
        stock_item_name="i",
        stock_level_name=None, stock_location_id=None, stock_location_breadcrumb=[],
        quantity=quantity, is_ticked=is_ticked, selected_product_id=selected_product_id,
        sequence=0, added_via="manual", added_at=datetime(2026, 1, 1),
        actual_unit_price=actual_unit_price, purchased_store_id=None,
        purchased_store_name=None, offers=list(offers),
    )


def test__single_unticked_line_price_and_savings():
    t = compute_list_totals([_line(quantity=2, offers=[_offer(2.0, 3.0)])])
    assert t.total_price == 4.0          # 2.0 * 2
    assert t.remaining_price == 4.0      # unticked
    assert t.total_savings == 2.0        # (3 - 2) * 2
    assert t.unticked_count == 1
    assert t.ticked_count == 0
    assert t.line_count == 1


def test__ticked_line_counts_in_total_but_not_remaining():
    lines = [
        _line(quantity=1, is_ticked=True, offers=[_offer(5.0, None)]),
        _line(quantity=1, is_ticked=False, offers=[_offer(3.0, None)]),
    ]
    t = compute_list_totals(lines)
    assert t.total_price == 8.0
    assert t.remaining_price == 3.0      # only the unticked line
    assert t.unticked_count == 1
    assert t.ticked_count == 1


def test__actual_price_override_wins_for_price_and_savings():
    # Paid 1.50 actual against an offer of price_now 2.0 / RRP 3.0.
    t = compute_list_totals([_line(quantity=1, actual_unit_price=1.5,
                                   offers=[_offer(2.0, 3.0)])])
    assert t.total_price == 1.5          # uses actual, not offer
    assert t.total_savings == 1.5        # (3.0 - 1.5) * 1


def test__no_offer_is_zero():
    t = compute_list_totals([_line(offers=[])])
    assert t.total_price == 0.0
    assert t.total_savings == 0.0


def test__no_price_was_means_no_savings():
    t = compute_list_totals([_line(offers=[_offer(2.0, None)])])
    assert t.total_price == 2.0
    assert t.total_savings == 0.0


def test__selected_offer_is_chosen_over_first():
    cheap = _offer(1.0, 2.0)                       # would be picked by offers[0]
    chosen = _offer(4.0, 6.0, is_selected=True)    # but this one is selected
    line = _line(quantity=1, offers=[cheap, chosen])
    t = compute_list_totals([line])
    assert t.total_price == 4.0          # the selected offer, not the cheaper first
    assert t.total_savings == 2.0        # 6 - 4


def test__negative_savings_floored_to_zero():
    # price_was below paid → no "savings".
    t = compute_list_totals([_line(offers=[_offer(5.0, 4.0)])])
    assert t.total_savings == 0.0


def test__none_quantity_treated_as_one():
    t = compute_list_totals([_line(quantity=None, offers=[_offer(2.5, None)])])
    assert t.total_price == 2.5


def test__empty_list_is_all_zero():
    t = compute_list_totals([])
    assert t.total_price == 0.0
    assert t.remaining_price == 0.0
    assert t.total_savings == 0.0
    assert t.unticked_count == 0
    assert t.ticked_count == 0
    assert t.line_count == 0
