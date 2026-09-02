"""FU-519 item 2 — reports router e2e (`dora_api/features/reports/reports.py`).

One test per report pinning the response shape plus at least one computed
value against data seeded through the API:

  stock-value-over-time · spend-by-store · most-bought-items ·
  keeps-running-out · price-trends · savings-captured · price-drops ·
  meals-cooked · spend-by-category · spend-year-over-year

`range=all` is used wherever ranges apply so assertions aren't sensitive to
the 30d default window; the actual→picked price ladder for spend-by-store is
already pinned by `test_spend_by_store.py` and not re-tested here.
"""
from uuid import uuid4

import pytest
import requests

from tests.e2e.dora_api._spend_seeding import seed_purchase
from tests.support import assert_problem, is_valid_datetime, set_money_enabled

BASE = "http://localhost:5170/api"
REPORTS = f"{BASE}/reports"

# Every report that answers in dollars refuses with 403 when the install has
# money off (FU-816 / R-058), and a fresh install has it off. The gate itself
# is exercised in its own region at the foot of this file.
@pytest.fixture(autouse=True)
def _money_on(api):
    set_money_enabled(True)


def _token() -> str:
    return f"zqr{uuid4().hex[:8]}"


#region ---------------- stock value over time ----------------


def test__stock_value_over_time__DefaultRange__DailyPointsWithEstimateNote(api):
    resp = requests.get(f"{REPORTS}/stock-value-over-time")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"range", "estimate_note", "points"}
    assert body["range"] == "30d"
    assert "Not accounting" in body["estimate_note"]
    assert body["points"], "seeded pantry should produce at least one bucket"
    for point in body["points"]:
        assert set(point.keys()) == {"date", "value"}
        assert point["value"] >= 0
    # Buckets are emitted oldest-first on a stable daily grid.
    dates = [p["date"] for p in body["points"]]
    assert dates == sorted(dates)


#endregion stock value over time

#region ---------------- spend by store ----------------


def test__spend_by_store__ArchivedPurchase__SpendIsPriceTimesQuantity(api):
    seeded = seed_purchase(price_now=4.5, quantity=2)

    rows = requests.get(f"{REPORTS}/spend-by-store", params={"range": "all"}).json()["rows"]

    row = next(r for r in rows if r["store_id"] == seeded["store_id"])
    assert set(row.keys()) == {
        "store_id", "store", "brand_colour", "spend", "list_count",
    }
    assert row["store"] == seeded["store_name"]
    assert row["spend"] == 9.0  # 4.5 picked × qty 2
    assert row["list_count"] == 1


def test__spend_by_store__Response__ShipsTotalAndStoreCountWithTheRows(api):
    # R-041 — a derived aggregate travels with its coverage. The dashboard's
    # spend card shows only the top 3 stores, so it must be able to say "top 3 of
    # N" and print a total it didn't compute itself. Before this, it summed the
    # fetched rows in the browser and rendered a bare "$X total" under three
    # rows, which reads as the sum of those three.
    seed_purchase(price_now=4.5, quantity=2)

    body = requests.get(f"{REPORTS}/spend-by-store", params={"range": "all"}).json()

    assert {"range", "rows", "total_spend", "store_count"} <= body.keys()
    assert body["store_count"] == len(body["rows"])
    # The total is the sum of every row, not just the ones a client might show.
    assert body["total_spend"] == pytest.approx(
        round(sum(r["spend"] for r in body["rows"]), 2)
    )
    assert body["total_spend"] >= 9.0


def test__spend_by_store__UsualStoreNoProduct__AttributedViaTheStoreLadder(api):
    # FU-815 — the handler used to require `selected_product_id IS NOT NULL`
    # and take the store off that product, i.e. rung five of the five-rung
    # ladder. A household that tags items "I buy this at Aldi" and never
    # touches the products feature therefore saw a populated store breakdown on
    # its receipt and an EMPTY card in Reports, off the same finished list.
    suffix = uuid4().hex[:8]
    store_name = f"LadderStore-{suffix}"
    assert requests.post(f"{BASE}/stores", json={"name": store_name}).status_code == 201
    stores = requests.get(f"{BASE}/stores").json()["items"]
    store_id = next(s["store_id"] for s in stores if s["name"] == store_name)

    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    item_resp = requests.post(f"{BASE}/stock-items", json={
        "name": f"LadderItem-{suffix}",
        "stock_level_id": level,
        "usual_store_id": store_id,
    })
    assert item_resp.status_code == 201, item_resp.text
    item_id = item_resp.json()["stock_item_id"]

    list_id = requests.post(
        f"{BASE}/shopping-lists", json={"name": f"LadderList-{suffix}"},
    ).json()["shopping_list_id"]
    # No `selected_product_id` — this line never touches the products feature.
    assert requests.post(
        f"{BASE}/shopping-lists/{list_id}/lines", json={"stock_item_id": item_id},
    ).status_code in (200, 201)
    line_id = requests.get(
        f"{BASE}/shopping-lists/{list_id}"
    ).json()["lines"][0]["line_id"]
    assert requests.patch(
        f"{BASE}/shopping-lists/{list_id}/lines/{line_id}",
        json={"is_ticked": True, "actual_unit_price": 7.25},
    ).status_code == 204
    assert requests.post(f"{BASE}/shopping-lists/{list_id}/finish").status_code == 200

    rows = requests.get(
        f"{REPORTS}/spend-by-store", params={"range": "all"},
    ).json()["rows"]

    row = next(r for r in rows if r["store_id"] == store_id)
    assert row["store"] == store_name
    assert row["spend"] == 7.25


def test__spend_by_store__TickedLineWithNoPrice__CountedAsUnpricedNotDropped(api):
    # R-041 — the total states what it was built from. Lines with no price at
    # all were (and still are) excluded from the money, but they used to vanish
    # without trace, so the card undercounted in silence while the shopping
    # list's own card said "12 items unpriced, not counted".
    seeded = seed_purchase(price_now=4.5)
    suffix = uuid4().hex[:8]
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    item_id = requests.post(f"{BASE}/stock-items", json={
        "name": f"UnpricedItem-{suffix}", "stock_level_id": level,
    }).json()["stock_item_id"]
    list_id = requests.post(
        f"{BASE}/shopping-lists", json={"name": f"UnpricedList-{suffix}"},
    ).json()["shopping_list_id"]
    requests.post(
        f"{BASE}/shopping-lists/{list_id}/lines", json={"stock_item_id": item_id},
    )
    line_id = requests.get(
        f"{BASE}/shopping-lists/{list_id}"
    ).json()["lines"][0]["line_id"]
    requests.patch(
        f"{BASE}/shopping-lists/{list_id}/lines/{line_id}", json={"is_ticked": True},
    )
    requests.post(f"{BASE}/shopping-lists/{list_id}/finish")

    body = requests.get(f"{REPORTS}/spend-by-store", params={"range": "all"}).json()

    assert body["unpriced_lines"] >= 1
    assert body["counted_lines"] >= 1
    # The unpriced line contributes nothing to the money.
    assert seeded["store_id"] in {r["store_id"] for r in body["rows"]}


#endregion spend by store

#region ---------------- most-bought items ----------------


def test__most_bought_items__ItemOnTwoArchivedLists__CountsDistinctLists(api):
    first = seed_purchase()
    # Same stock item on a second archived list → appearances = 2 (distinct
    # lists, not line edits).
    seed_purchase(stock_item_id=first["stock_item_id"])

    rows = requests.get(
        f"{REPORTS}/most-bought-items", params={"range": "all", "limit": 50},
    ).json()["rows"]

    row = next(r for r in rows if r["stock_item_id"] == first["stock_item_id"])
    assert set(row.keys()) == {"stock_item_id", "name", "appearances"}
    assert row["name"] == first["stock_item_name"]
    assert row["appearances"] == 2


#endregion most-bought items

#region ---------------- keeps running out ----------------


def _add_to_new_list(token: str, item_id: str, list_name: str) -> None:
    list_id = requests.post(
        f"{BASE}/shopping-lists", json={"name": f"{token} {list_name}"},
    ).json()["shopping_list_id"]
    line = requests.post(
        f"{BASE}/shopping-lists/{list_id}/lines", json={"stock_item_id": item_id},
    )
    assert line.status_code in (200, 201), line.text


def test__keeps_running_out__ItemDroppedToOutThenAdded__Tallied(api):
    token = _token()
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    out_level = next(l for l in levels if l["sequence"] == 2)
    stocked_level = next(l for l in levels if l["sequence"] == 0)
    item_resp = requests.post(f"{BASE}/stock-items", json={
        "name": f"{token} tonic", "stock_level_id": stocked_level["stock_level_id"],
    })
    assert item_resp.status_code == 201, item_resp.text
    item_id = item_resp.json()["stock_item_id"]
    # Drop to Out via the update endpoint so a StockLevelChange transition is
    # logged, then add to a list — "added while out" is the report's signal.
    drop = requests.patch(f"{BASE}/stock-items/{item_id}", json={
        "stock_level_id": out_level["stock_level_id"],
    })
    assert drop.status_code in (200, 204), drop.text
    _add_to_new_list(token, item_id, "restock")

    rows = requests.get(
        f"{REPORTS}/keeps-running-out", params={"limit": 50},
    ).json()["rows"]

    row = next(r for r in rows if r["stock_item_id"] == item_id)
    assert set(row.keys()) == {"stock_item_id", "name", "times_out_when_added"}
    assert row["times_out_when_added"] == 1


# Regression for the FU-527 fix (2026-07-12): the fallback items query now
# `.include(STOCK_LEVEL)`, so an item with no change-log history falls back to
# its current level and is tallied instead of silently dropped.
def test__keeps_running_out__ItemCreatedOutWithNoLevelHistory__FallbackTallies(api):
    token = _token()
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    out_level = next(l for l in levels if l["sequence"] == 2)
    item_resp = requests.post(f"{BASE}/stock-items", json={
        "name": f"{token} bitters", "stock_level_id": out_level["stock_level_id"],
    })
    assert item_resp.status_code == 201, item_resp.text
    item_id = item_resp.json()["stock_item_id"]
    _add_to_new_list(token, item_id, "restock")

    rows = requests.get(
        f"{REPORTS}/keeps-running-out", params={"limit": 50},
    ).json()["rows"]

    assert item_id in {r["stock_item_id"] for r in rows}


def test__keeps_running_out__Range__BoundsWhichAddsCount(api):
    # REPORTS_PAGE_REVIEW.md §3.5 / D7 — the card sits directly under the
    # range picker and used to count all history, forever, while wearing a
    # label that said "30 days". An add that happened just now is inside every
    # window; the point of this test is that the parameter is honoured at all
    # and that an omitted one still means all-time, which is what the
    # dashboard's restock radar relies on.
    token = _token()
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    out_level = next(l for l in levels if l["sequence"] == 2)
    item_id = requests.post(f"{BASE}/stock-items", json={
        "name": f"{token} anchovies", "stock_level_id": out_level["stock_level_id"],
    }).json()["stock_item_id"]
    _add_to_new_list(token, item_id, "restock")

    bounded = requests.get(
        f"{REPORTS}/keeps-running-out", params={"limit": 50, "range": "30d"},
    ).json()
    unbounded = requests.get(
        f"{REPORTS}/keeps-running-out", params={"limit": 50},
    ).json()

    assert bounded["range"] == "30d"
    assert item_id in {r["stock_item_id"] for r in bounded["rows"]}
    # No `range` param ⇒ all time, the pre-FU-816 meaning.
    assert unbounded["range"] == "all"
    assert item_id in {r["stock_item_id"] for r in unbounded["rows"]}


#endregion keeps running out

#region ---------------- price trends ----------------


def test__price_trends__ProductWithCurrentOffer__SingleSeriesSinglePoint(api):
    seeded = seed_purchase(price_now=4.5, finish=False, tick=False)

    body = requests.get(f"{REPORTS}/price-trends", params={
        "product_ids": seeded["product_id"], "range": "all",
    }).json()

    assert set(body.keys()) == {"range", "series"}
    assert len(body["series"]) == 1
    series = body["series"][0]
    assert series["product_id"] == seeded["product_id"]
    assert series["store"] == seeded["store_name"]
    assert [p["unit_price"] for p in series["points"]] == [4.5]


@pytest.mark.parametrize("bounded_range", ["30d", "90d", "1y"])
def test__price_trends__BoundedRange__DoesNotCrashOnNaiveOfferTimestamps(
    api, bounded_range,
):
    # FU-813 regression. `offered_on` is `DateTime(timezone=True)`, but SQLite
    # does not preserve tzinfo, so it came back naive and was compared against
    # an aware `since` — `TypeError`, i.e. a 500 on every range except "All
    # time". It went unnoticed because the only seeded price-trends test above
    # passes `range=all`, the one branch where `since is None` and the
    # comparison never executes. It would also have passed on Postgres, which
    # makes it a §7.5 portability break as well as a crash.
    seeded = seed_purchase(price_now=4.5, finish=False, tick=False)

    resp = requests.get(f"{REPORTS}/price-trends", params={
        "product_ids": seeded["product_id"], "range": bounded_range,
    })

    assert resp.status_code == 200, resp.text
    series = resp.json()["series"][0]
    # The offer was created just now, so a bounded window still contains it.
    assert [p["unit_price"] for p in series["points"]] == [4.5]


def test__price_trends__NoProductIds__EmptySeries(api):
    body = requests.get(f"{REPORTS}/price-trends").json()

    assert body["series"] == []


def test__price_trends__MalformedProductId__BadRequest(api):
    resp = requests.get(
        f"{REPORTS}/price-trends", params={"product_ids": "not-a-uuid"},
    )

    assert_problem(resp, 400, title="Invalid product_ids")


#endregion price trends

#region ---------------- savings captured ----------------


def test__savings_captured__PickedBelowRrpSnapshot__SavingsIsDelta(api):
    # picked_offer_price=4.5 / list_price_at_pick=10.5 snapshotted at add time.
    seeded = seed_purchase(price_now=4.5, price_was=10.5)

    body = requests.get(
        f"{REPORTS}/savings-captured", params={"range": "all"},
    ).json()

    assert set(body.keys()) == {"total_savings", "total_spent", "lists", "range"}
    entry = next(
        l for l in body["lists"]
        if l["shopping_list_id"] == seeded["shopping_list_id"]
    )
    assert entry["picked_total"] == 4.5
    assert entry["list_total"] == 10.5
    assert entry["savings"] == 6.0
    assert is_valid_datetime(entry["completed_at"])
    assert body["total_savings"] >= 6.0
    assert body["total_spent"] >= 4.5


#endregion savings captured

#region ---------------- price drops ----------------


def test__price_drops__CurrentOfferBelowAllHistory__ReportedAsNewLow(api):
    seeded = seed_purchase(price_now=10.0, price_was=12.0, finish=False, tick=False)
    # A price update archives the prior offer → historic low = 10.0.
    patch = requests.patch(f"{BASE}/products/{seeded['product_id']}", json={
        "price_now": 8.0, "price_was": 12.0,
    })
    assert patch.status_code in (200, 204), patch.text

    rows = requests.get(f"{REPORTS}/price-drops", params={"limit": 20}).json()["rows"]

    row = next(r for r in rows if r["product_id"] == seeded["product_id"])
    assert set(row.keys()) == {
        "product_id", "name", "store_id", "store_name", "has_image",
        "price_now", "previous_low", "drop_amount", "drop_percent",
        "linked_stock_item_id", "linked_stock_item_name",
    }
    assert row["price_now"] == 8.0
    assert row["previous_low"] == 10.0
    assert row["drop_amount"] == 2.0
    assert row["drop_percent"] == 20
    assert row["store_name"] == seeded["store_name"]


def test__price_drops__ProductWithNoHistory__NeverANewLow(api):
    # Only one price ever seen → "new low" would be dishonest (Honesty §2.4).
    seeded = seed_purchase(price_now=1.0, price_was=2.0, finish=False, tick=False)

    rows = requests.get(f"{REPORTS}/price-drops", params={"limit": 20}).json()["rows"]

    assert seeded["product_id"] not in {r["product_id"] for r in rows}


def _seed_drop(price_from: float, price_to: float) -> str:
    """One tracked product whose current offer is a new low: created at
    ``price_from`` (archived to history by the PATCH), now ``price_to``.
    Returns the product id."""
    seeded = seed_purchase(price_now=price_from, price_was=price_from + 2.0,
                           finish=False, tick=False)
    patch = requests.patch(f"{BASE}/products/{seeded['product_id']}", json={
        "price_now": price_to, "price_was": price_from + 2.0,
    })
    assert patch.status_code in (200, 204), patch.text
    return seeded["product_id"]


def test__price_drops__Ranking__PercentDescThenAmountDesc(api):
    # 50% off ranks over 20% off; between the two 20%s, the bigger dollar
    # drop ($4 on 20→16) ranks over the smaller ($2 on 10→8).
    big_pct = _seed_drop(10.0, 5.0)      # 50%, $5
    tie_small = _seed_drop(10.0, 8.0)    # 20%, $2
    tie_big = _seed_drop(20.0, 16.0)     # 20%, $4

    rows = requests.get(f"{REPORTS}/price-drops", params={"limit": 20}).json()["rows"]

    ours = [r["product_id"] for r in rows
            if r["product_id"] in {big_pct, tie_small, tie_big}]
    assert ours == [big_pct, tie_big, tie_small]


def test__price_drops__InactiveProduct__Excluded(api):
    product_id = _seed_drop(10.0, 8.0)
    rows = requests.get(f"{REPORTS}/price-drops", params={"limit": 20}).json()["rows"]
    assert product_id in {r["product_id"] for r in rows}

    patch = requests.patch(f"{BASE}/products/{product_id}", json={"is_active": False})
    assert patch.status_code in (200, 204), patch.text

    rows = requests.get(f"{REPORTS}/price-drops", params={"limit": 20}).json()["rows"]
    assert product_id not in {r["product_id"] for r in rows}


def test__price_drops__LimitClampsToOneThroughTwenty__DefaultFive(api):
    # Six genuine drops on the board so the default-5 slice is observable.
    for i in range(6):
        _seed_drop(10.0 + i, 5.0)

    assert len(requests.get(f"{REPORTS}/price-drops", params={"limit": "0"}).json()["rows"]) == 1
    assert len(requests.get(f"{REPORTS}/price-drops", params={"limit": "-3"}).json()["rows"]) == 1
    assert len(requests.get(f"{REPORTS}/price-drops", params={"limit": "999"}).json()["rows"]) <= 20
    # Missing or unparseable limit → the default 5.
    assert len(requests.get(f"{REPORTS}/price-drops").json()["rows"]) == 5
    assert len(requests.get(f"{REPORTS}/price-drops", params={"limit": "abc"}).json()["rows"]) == 5


#endregion price drops

#region ---------------- meals cooked ----------------


def test__meals_cooked__RecipeCookedTwice__CountsEventsAndPortionsSeparately(api):
    token = _token()
    recipe = requests.post(f"{BASE}/recipes", json={"name": f"{token} stew"})
    assert recipe.status_code == 201, recipe.text
    recipe_id = recipe.json()["recipe_id"]
    for meals in (3, 2):
        cook = requests.post(
            f"{BASE}/recipes/{recipe_id}/cook", json={"meals_cooked": meals},
        )
        assert cook.status_code == 200, cook.text

    body = requests.get(
        f"{REPORTS}/meals-cooked", params={"range": "all", "limit": 50},
    ).json()

    assert set(body.keys()) == {
        "range", "cook_count", "meals_total", "top_recipes", "timeline",
    }
    top = next(r for r in body["top_recipes"] if r["recipe_id"] == recipe_id)
    assert top["recipe_name"] == f"{token} stew"
    assert top["cook_count"] == 2      # two cooking sessions...
    assert top["meals_total"] == 5     # ...feeding five meals total
    assert body["cook_count"] >= 2
    assert body["meals_total"] >= 5
    assert sum(p["cook_count"] for p in body["timeline"]) == body["cook_count"]


#endregion meals cooked

#region ---------------- spend by category ----------------


def test__spend_by_category__ItemWithStockGroup__BucketsUnderGroupName(api):
    token = _token()
    group = requests.post(f"{BASE}/stock-groups", json={"name": f"{token} snacks"})
    assert group.status_code == 201, group.text
    seed_purchase(price_now=4.5, stock_group_id=group.json()["stock_group_id"])

    body = requests.get(
        f"{REPORTS}/spend-by-category", params={"range": "all"},
    ).json()

    assert set(body.keys()) == {"range", "total_spent", "rows"}
    row = next(r for r in body["rows"] if r["category"] == f"{token} snacks")
    assert set(row.keys()) == {"category", "spent", "item_count", "share_pct"}
    assert row["spent"] == 4.5
    assert row["item_count"] == 1
    assert 0 < row["share_pct"] <= 100
    assert body["total_spent"] >= 4.5


#endregion spend by category

#region ---------------- spend year-over-year ----------------


def test__spend_year_over_year__NewCategoryThisWindow__NoRateOfChangeClaimed(api):
    token = _token()
    group = requests.post(f"{BASE}/stock-groups", json={"name": f"{token} treats"})
    assert group.status_code == 201, group.text
    seed_purchase(price_now=4.5, stock_group_id=group.json()["stock_group_id"])

    body = requests.get(f"{REPORTS}/spend-year-over-year").json()

    assert set(body.keys()) == {
        "range", "window_days", "current_total", "previous_total",
        "delta", "delta_pct", "rows",
    }
    assert body["range"] == "1y"
    assert body["window_days"] == 365
    row = next(r for r in body["rows"] if r["category"] == f"{token} treats")
    assert row["current"] == 4.5
    assert row["previous"] == 0.0
    assert row["delta"] == 4.5
    # No prior spend → delta_pct is None, never "+∞%" (P3 Honest).
    assert row["delta_pct"] is None


def test__spend_year_over_year__RangeAll__RejectedAsUnbounded(api):
    resp = requests.get(f"{REPORTS}/spend-year-over-year", params={"range": "all"})

    assert_problem(resp, 400, title="range=all is not supported")


#endregion spend year-over-year

#region ---------------- money gate ----------------


# FU-816 / R-058 — every report that answers in dollars refuses outright when
# the install has money off. Gating the render alone was the state this page
# was in before: `ReportsPage.vue` imported no feature flag at all, so an
# install that had opted out still got spend by store, savings, spend by
# category, year-over-year and two dollar-formatted chart axes.
_MONEY_GATED = [
    ("stock-value-over-time", {}),
    ("spend-by-store", {}),
    ("savings-captured", {}),
    ("spend-by-category", {}),
    ("spend-year-over-year", {}),
    ("price-trends", {"product_ids": ""}),
]


@pytest.mark.parametrize("path,params", _MONEY_GATED)
def test__money_reports__MoneyDisabled__Forbidden(api, path, params):
    set_money_enabled(False)

    resp = requests.get(f"{REPORTS}/{path}", params=params)

    assert_problem(resp, 403, detail="money features are turned off")


# The counting reports are deliberately NOT gated: they are what keeps
# `/reports` worth a nav entry on a money-off install, which is why the nav
# entry stays unconditional.
@pytest.mark.parametrize(
    "path", ["most-bought-items", "keeps-running-out", "meals-cooked"],
)
def test__counting_reports__MoneyDisabled__StillAnswer(api, path):
    set_money_enabled(False)

    resp = requests.get(f"{REPORTS}/{path}")

    assert resp.status_code == 200, resp.text


#endregion money gate
