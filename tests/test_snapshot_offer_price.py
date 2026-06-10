"""Unit tests for the offer-price snapshot helper (State Ownership Chunk 6).

The snapshot freezes the current offer onto a shopping-list line at the
*commit-to-offer* moment (add with `selected_product_id`, or later
selection-change), so historic reporting stays honest if prices move
before the line is ticked. The helper itself is the unit; the timing
rules around when it's called live in the AddLine / UpdateLine handlers.
"""
from types import SimpleNamespace
from uuid import uuid4

from dora_api.features.shopping_lists.manage_shopping_list_lines import \
    snapshot_offer_price


class _OneQuery:
    def __init__(self, hit):
        self._hit = hit

    def one(self, *_args, **_kwargs):
        return self._hit


class _FakeRepo:
    """Returns a fixed `ProductOffer` for any `.get(ProductOffer).one(...)`."""

    def __init__(self, offer):
        self._offer = offer

    def get(self, _entity):
        return _OneQuery(self._offer)


def _offer(price_now: float, price_was: float | None) -> SimpleNamespace:
    return SimpleNamespace(price_now=price_now, price_was=price_was)


def _line(selected_product_id):
    return SimpleNamespace(
        id=uuid4(),
        selected_product_id=selected_product_id,
        picked_offer_price=None,
        list_price_at_pick=None,
    )


def test__snapshot_sets_both_prices_when_offer_has_was():
    line = _line(selected_product_id=uuid4())
    repo = _FakeRepo(offer=_offer(price_now=4.5, price_was=6.0))

    snapshot_offer_price(repo, line)

    assert line.picked_offer_price == 4.5
    assert line.list_price_at_pick == 6.0


def test__snapshot_leaves_list_price_none_when_offer_has_no_was():
    line = _line(selected_product_id=uuid4())
    repo = _FakeRepo(offer=_offer(price_now=2.99, price_was=None))

    snapshot_offer_price(repo, line)

    assert line.picked_offer_price == 2.99
    assert line.list_price_at_pick is None


def test__snapshot_is_a_noop_when_no_selected_product():
    line = _line(selected_product_id=None)
    repo = _FakeRepo(offer=_offer(price_now=4.5, price_was=6.0))

    snapshot_offer_price(repo, line)

    assert line.picked_offer_price is None
    assert line.list_price_at_pick is None


def test__snapshot_is_a_noop_when_no_offer_exists_for_product():
    line = _line(selected_product_id=uuid4())
    repo = _FakeRepo(offer=None)

    snapshot_offer_price(repo, line)

    assert line.picked_offer_price is None
    assert line.list_price_at_pick is None
