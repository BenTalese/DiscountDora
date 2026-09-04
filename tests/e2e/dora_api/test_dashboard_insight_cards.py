"""Owner feedback 2026-09-04 — the four endpoints behind the reworked dashboard.

`/dashboard/use-it-up`, `/dashboard/before-you-shop`, `/dashboard/lists` and
`/dashboard/restock-radar`.

**Why these have tests when the verification stance is manual-first**
(`DORA_VERIFY_TRIAGE.md`): the stance says automate only what pins a *stable,
low-churn contract that is expensive to re-check by hand*. The card layouts are
neither — they will churn, and they are trivial to eyeball. But each of these
endpoints has exactly one rule that is invisible in a browser and expensive to
set up by hand:

  use-it-up        a recipe is listed only if it *requires* an expiring item —
                   an optional ingredient must not pull it in.
  before-you-shop  a low item on an active list must NOT appear. This is the
                   whole reason the card exists rather than restating the bell,
                   and eyeballing it means building a list mid-verify.
  lists            "current" prefers a list somebody pressed Start shopping on,
                   over any draft, whatever the dates say.
  restock-radar    only items *currently* in the band — an item that went out
                   and was restocked must drop off.

Get any of those wrong and the card still renders plausibly, which is precisely
the failure a manual walk misses.

Delta-style like `test_dashboard_router.py`: create through the real endpoints
and assert on the rows we created, so the seeded dataset never leaks into an
expectation.
"""
from datetime import timedelta
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
USE_IT_UP = f"{BASE}/dashboard/use-it-up"
BEFORE_YOU_SHOP = f"{BASE}/dashboard/before-you-shop"
LISTS = f"{BASE}/dashboard/lists"
RESTOCK_RADAR = f"{BASE}/dashboard/restock-radar"
STOCK_ITEMS = f"{BASE}/stock-items"
SHOPPING_LISTS = f"{BASE}/shopping-lists"
RECIPES = f"{BASE}/recipes"
MEAL_PLANS = f"{BASE}/meal-plans"

#region ---------------- helpers ----------------


def _today():
    from datetime import date
    return date.fromisoformat(requests.get(f"{MEAL_PLANS}/today").json()["today"])


def _stock_level_id(sequence: int) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _make_item(**body) -> dict:
    """Create a stock item. `stock_level_id` is required by the endpoint, so it
    defaults to Stocked here — the expiry tests care about dates, not levels.

    ⚠️ Every card under test shows a **top-N slice** of a seeded dataset that
    already fills it (5 running-out rows, 4-5 per restock column, 4 use-it-up
    items). A freshly created item is therefore only observable if it out-ranks
    the seed under that card's own sort. Each test below says how it does that;
    an assertion that "my item is in the list" without that consideration is the
    trap this note exists to stop.
    """
    payload = {
        "name": f"Insight Item {uuid4().hex[:8]}",
        "stock_level_id": _stock_level_id(0),
        **body,
    }
    resp = requests.post(STOCK_ITEMS, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _names(rows) -> set[str]:
    return {r["name"] for r in rows}

#endregion helpers

#region ---------------- use-it-up ----------------


def test__use_it_up__ResponseShape__CarriesItemsRecipesAndWindow(api):
    body = requests.get(USE_IT_UP).json()
    assert body.keys() == {"items", "recipes", "window_days"}
    # The window is the household's own `expiring_soon_window_days`, so the card
    # can name it rather than hardcoding "this week" over a setting that might
    # say 3 or 30.
    assert isinstance(body["window_days"], int) and body["window_days"] >= 1


def test__use_it_up__ItemExpiringInsideWindow__IsListedWithDaysRemaining(api):
    # Dated today so it sorts near the front of the seeded set (which runs from
    # 3 days expired to 4 days out) and can't be pushed off the 5-row slice.
    # Today is also the interesting boundary: still usable, no days left.
    due = _today()
    item = _make_item(expiry_date=due.isoformat())

    rows = requests.get(USE_IT_UP).json()["items"]
    mine = next(r for r in rows if r["stock_item_id"] == item["stock_item_id"])
    assert mine["days_remaining"] == 0
    # `is_expired` is strictly *past* its date — an item due today has not
    # expired, and rendering it as a loss would be wrong by a day.
    assert mine["is_expired"] is False


def test__use_it_up__ItemExpiringBeyondWindow__IsNotListed(api):
    window = requests.get(USE_IT_UP).json()["window_days"]
    far = _today() + timedelta(days=window + 30)
    item = _make_item(expiry_date=far.isoformat())

    rows = requests.get(USE_IT_UP).json()["items"]
    assert item["stock_item_id"] not in {r["stock_item_id"] for r in rows}


def test__use_it_up__OptionalIngredient__DoesNotPullTheRecipeIn(api):
    """The rule a browser can't show you.

    "Recipes that use it up" has to mean *require*. A recipe that lists the
    expiring item as optional does not use it up — you'd cook it and the
    spinach would still be there — so suggesting it would be a lie in exactly
    the situation the card exists for.
    """
    # Expired a week ago: sorts to the very front, so both probe recipes are
    # certain to be evaluated against a listed item.
    item = _make_item(expiry_date=(_today() - timedelta(days=7)).isoformat())
    required = requests.post(RECIPES, json={
        "name": f"Requires It {uuid4().hex[:8]}",
        "ingredients": [
            {"raw_text": item["name"], "stock_item_id": item["stock_item_id"]},
        ],
    })
    assert required.status_code == 201, required.text
    optional = requests.post(RECIPES, json={
        "name": f"Optional Only {uuid4().hex[:8]}",
        "ingredients": [
            {
                "raw_text": item["name"],
                "stock_item_id": item["stock_item_id"],
                "is_optional": True,
            },
        ],
    })
    assert optional.status_code == 201, optional.text

    listed = _names(requests.get(USE_IT_UP).json()["recipes"])
    assert required.json()["name"] in listed
    assert optional.json()["name"] not in listed

#endregion use-it-up

#region ---------------- before-you-shop ----------------


def test__before_you_shop__ResponseShape__CarriesBothHalvesAndShopTiming(api):
    body = requests.get(BEFORE_YOU_SHOP).json()
    assert body.keys() == {"running_out", "plan_gaps", "shop_in_days"}


def test__before_you_shop__OutAndEssential__IsListedFirst(api):
    # The sort is (out before low, essential before not, then name), and none of
    # the seeded rows is essential — so an essential out-of-stock item is the
    # top row by construction, which is both the assertion and how it survives
    # the 5-row slice.
    item = _make_item(stock_level_id=_stock_level_id(2), is_essential=True)

    rows = requests.get(BEFORE_YOU_SHOP).json()["running_out"]
    assert rows[0]["stock_item_id"] == item["stock_item_id"]
    assert rows[0]["band"] == "out"
    assert rows[0]["is_essential"] is True


def test__before_you_shop__OutRanksLow__AndBandIsReported(api):
    rows = requests.get(BEFORE_YOU_SHOP).json()["running_out"]
    # The ordering promise the card leans on: the worse state reads first, so
    # no "low" row may precede an "out" row. Asserted over whatever the dataset
    # holds rather than a planted item — it is a property of the list, not of
    # any one row.
    bands = [r["band"] for r in rows]
    assert bands == sorted(bands, key=lambda b: b != "out")


def test__before_you_shop__ItemAlreadyOnAnActiveList__DropsOut(api):
    """**The** rule of this card.

    The alerts bell and the stock page both keep saying "you're low on flour"
    after you have added it to Saturday's list. This card is the one surface
    that knows the difference, and if this filter breaks the card silently
    becomes a third copy of the bell — which is what the owner deleted the
    attention card for.
    """
    # Essential + out for the same top-of-slice reason as above.
    item = _make_item(stock_level_id=_stock_level_id(2), is_essential=True)
    before = requests.get(BEFORE_YOU_SHOP).json()["running_out"]
    assert item["stock_item_id"] in {r["stock_item_id"] for r in before}

    lst = requests.post(SHOPPING_LISTS, json={"name": f"Gap List {uuid4().hex[:8]}"})
    assert lst.status_code == 201, lst.text
    line = requests.post(
        f"{SHOPPING_LISTS}/{lst.json()['shopping_list_id']}/lines",
        json={"stock_item_id": item["stock_item_id"], "quantity": 1},
    )
    # POST /lines returns 200 with `{already_on_list, line_id}` — the add is
    # idempotent, so it reports what happened rather than always claiming 201.
    assert line.status_code == 200, line.text

    after = requests.get(BEFORE_YOU_SHOP).json()["running_out"]
    assert item["stock_item_id"] not in {r["stock_item_id"] for r in after}

#endregion before-you-shop

#region ---------------- lists ----------------


def test__dashboard_lists__ResponseShape__CarriesThreeTenses(api):
    body = requests.get(LISTS).json()
    assert body.keys() == {"current", "next", "finished"}


def test__dashboard_lists__ShoppingListWins__OverAnyDraft(api):
    """A list somebody pressed Start shopping on is "current", full stop.

    Date-based, a draft planned for today would outrank a shopping list started
    yesterday — and the one you are holding in the supermarket is obviously the
    current one. Invisible in a browser unless you build both lists first.
    """
    # The seed already has a list in the `shopping` state; plant a draft dated
    # *today*, which is the one that would win on dates alone, and assert the
    # in-flight list still holds `current`.
    started = requests.post(SHOPPING_LISTS, json={
        "name": f"In Flight {uuid4().hex[:8]}",
    })
    assert started.status_code == 201, started.text
    started_id = started.json()["shopping_list_id"]
    # PATCH status returns 204 No Content — a status edit is not a read.
    begin = requests.patch(
        f"{SHOPPING_LISTS}/{started_id}", json={"status": "shopping"},
    )
    assert begin.status_code == 204, begin.text

    soon = requests.post(SHOPPING_LISTS, json={
        "name": f"Sooner Draft {uuid4().hex[:8]}",
        "planned_shop_date": _today().isoformat(),
    })
    assert soon.status_code == 201, soon.text

    current = requests.get(LISTS).json()["current"]
    assert current is not None
    assert current["status"] == "shopping"
    assert current["shopping_list_id"] != soon.json()["shopping_list_id"]


def test__dashboard_lists__CardCarriesTheTotalsTheCardRenders(api):
    """The card renders five fields off each pick; a missing one is a blank row.

    Asserted over the seed's own three lists rather than a planted one: which
    list lands in which slot is the endpoint's decision, so a test that plants a
    list and then hunts for it is really testing the picker twice. The picker
    has its own test above.
    """
    body = requests.get(LISTS).json()
    cards = [c for c in (body["current"], body["next"], body["finished"]) if c]
    assert cards, "the seeded dataset should fill at least one slot"

    for card in cards:
        for field in (
            "shopping_list_id", "display_name", "status", "effective_date",
            "line_count", "unticked_count",
            "remaining_price", "total_price", "total_savings",
        ):
            assert field in card, f"{field} missing from {card.get('display_name')}"
    # A finished list reports what it cost; an open one what is left to grab.
    # Both numbers travel, because the card renders a different one per tense.
    if body["finished"]:
        assert body["finished"]["status"] == "done"

#endregion lists

#region ---------------- restock radar ----------------


def test__restock_radar__ResponseShape__CarriesBothColumns(api):
    body = requests.get(RESTOCK_RADAR).json()
    assert body.keys() == {"recently_out", "recently_low"}


def test__restock_radar__SortsIntoTheRightColumn(api):
    out_item = _make_item(stock_level_id=_stock_level_id(2))
    low_item = _make_item(stock_level_id=_stock_level_id(1))

    body = requests.get(RESTOCK_RADAR).json()
    assert out_item["stock_item_id"] in {r["stock_item_id"] for r in body["recently_out"]}
    assert low_item["stock_item_id"] in {r["stock_item_id"] for r in body["recently_low"]}


def test__restock_radar__RestockedItem__LeavesTheRadar(api):
    """Present tense, not history.

    "Recently ran out" about something you have since restocked is a diary
    entry, not a restock cue — and it is the failure mode the old lifetime
    ranking had, where the card looked identical week after week.
    """
    item = _make_item(stock_level_id=_stock_level_id(2))
    out_ids = {
        r["stock_item_id"] for r in requests.get(RESTOCK_RADAR).json()["recently_out"]
    }
    assert item["stock_item_id"] in out_ids

    restock = requests.patch(
        f"{STOCK_ITEMS}/{item['stock_item_id']}",
        json={"stock_level_id": _stock_level_id(0)},
    )
    assert restock.status_code == 204, restock.text

    body = requests.get(RESTOCK_RADAR).json()
    assert item["stock_item_id"] not in {r["stock_item_id"] for r in body["recently_out"]}
    assert item["stock_item_id"] not in {r["stock_item_id"] for r in body["recently_low"]}

#endregion restock radar
