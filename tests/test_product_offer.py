"""Unit tests for the server discount rule (best-deals ranking, Type B / FU-053).

Mirrors the client `discountPercent` (scrapedProductOfferLogic.ts): only genuine
specials get a percent; everything else is None (filtered out of best-deals).
"""
from dora_api.domain.product_offer import discount_percent


def test__genuine_special_returns_whole_percent():
    assert discount_percent(2.0, 3.0) == 33   # round((3-2)/3*100)
    assert discount_percent(5.0, 10.0) == 50
    assert discount_percent(7.5, 10.0) == 25


def test__not_on_special_is_none():
    assert discount_percent(5.0, 4.0) is None    # now > was
    assert discount_percent(3.0, 3.0) is None     # equal — no discount
    assert discount_percent(3.0, 0) is None       # no RRP


def test__missing_or_zero_prices_are_none():
    assert discount_percent(None, 3.0) is None
    assert discount_percent(2.0, None) is None
    assert discount_percent(0, 3.0) is None
    assert discount_percent(2.0, 0) is None
