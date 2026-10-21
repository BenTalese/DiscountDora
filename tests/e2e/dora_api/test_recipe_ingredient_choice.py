"""A recipe ingredient can say which one of its stock item it means.

Under "Cheese" a recipe can ask for "tasty cheddar" (a name of its own), one
of the item's preferred buys, or one of its linked products. The label is the
displayed name; picks must belong to the item; unlinking the product clears
it; a new version keeps the choice; a shopping line can start with the pick.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
RECIPES = f"{BASE}/recipes"
STOCK_ITEMS = f"{BASE}/stock-items"


def _stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == 0)


def _new_item() -> str:
    return make_stock_item(stock_level_id=_stock_level_id(),
                           name=f"IngChoiceItem {uuid4().hex[:8]}")["stock_item_id"]


def _make_product() -> str:
    suffix = uuid4().hex[:8]
    resp = requests.post(f"{BASE}/products", json={
        "name": f"IngChoiceProduct-{suffix}",
        "store_name": "Woolworths",
        "merchant_stockcode": f"ING-{suffix}",
        "brand": "Test",
        "price_now": 3.0,
        "price_was": 4.0,
        "is_active": True,
        "is_available": True,
        "size": "1L",
        "size_unit": "L",
        "size_value": 1.0,
    })
    assert resp.status_code == 201, resp.text
    return resp.headers["location"].rsplit(":", 1)[-1]


def _preferred_buy(item_id: str, label: str) -> str:
    requests.post(f"{STOCK_ITEMS}/{item_id}/preferred-buys", json={"label": label})
    detail = requests.get(f"{STOCK_ITEMS}/{item_id}/detail").json()
    return next(pb["preferred_buy_id"] for pb in detail["preferred_buys"] if pb["label"] == label)


def _create(ingredient: dict) -> requests.Response:
    return requests.post(RECIPES, json={
        "name": f"IngChoice {uuid4().hex[:8]}",
        "ingredients": [ingredient],
    })


def _ingredient(recipe_id: str) -> dict:
    return requests.get(f"{RECIPES}/{recipe_id}").json()["ingredients"][0]


def test__label__is_trimmed_and_round_trips(api):
    item = _new_item()
    resp = _create({"stock_item_id": item, "label": "  tasty cheddar  "})
    assert resp.status_code == 201, resp.text

    assert _ingredient(resp.json()["recipe_id"])["label"] == "tasty cheddar"


def test__blank_label__is_stored_as_null(api):
    resp = _create({"stock_item_id": _new_item(), "label": "   "})
    assert _ingredient(resp.json()["recipe_id"])["label"] is None


def test__preferred_buy__round_trips_and_survives_a_version(api):
    item = _new_item()
    pb = _preferred_buy(item, "Bega Tasty")
    resp = _create({"stock_item_id": item, "preferred_buy_id": pb, "label": "cheddar"})
    recipe_id = resp.json()["recipe_id"]

    assert _ingredient(recipe_id)["preferred_buy_id"] == pb

    version = requests.post(f"{RECIPES}/{recipe_id}/new-version", json={})
    assert version.status_code in (200, 201), version.text
    copy = _ingredient(version.json()["recipe_id"])
    assert copy["preferred_buy_id"] == pb
    assert copy["label"] == "cheddar"


def test__another_items_preferred_buy__is_rejected(api):
    other_pb = _preferred_buy(_new_item(), "Somebody else's")
    resp = _create({"stock_item_id": _new_item(), "preferred_buy_id": other_pb})
    assert resp.status_code == 422, resp.text


def test__pick_on_an_unlinked_row__is_rejected(api):
    pb = _preferred_buy(_new_item(), "Orphan")
    resp = _create({"raw_text": "some cheese", "preferred_buy_id": pb})
    assert resp.status_code == 422, resp.text


def test__product__round_trips_and_clears_on_unlink(api):
    item = _new_item()
    product = _make_product()
    assert requests.post(f"{STOCK_ITEMS}/{item}/products", json={"product_id": product}).status_code in (200, 204)
    resp = _create({"stock_item_id": item, "selected_product_id": product, "label": "cheddar"})
    assert resp.status_code == 201, resp.text
    recipe_id = resp.json()["recipe_id"]
    assert _ingredient(recipe_id)["selected_product_id"] == product

    assert requests.delete(f"{STOCK_ITEMS}/{item}/products/{product}").status_code == 204

    ing = _ingredient(recipe_id)
    assert ing["selected_product_id"] is None
    assert ing["label"] == "cheddar"


def test__unlinked_product__is_rejected(api):
    resp = _create({"stock_item_id": _new_item(), "selected_product_id": _make_product()})
    assert resp.status_code == 422, resp.text


def test__update__replaces_the_choice(api):
    item = _new_item()
    recipe_id = _create({"stock_item_id": item, "label": "cheddar"}).json()["recipe_id"]

    resp = requests.patch(f"{RECIPES}/{recipe_id}", json={
        "ingredients": [{"stock_item_id": item, "label": "mozzarella"}],
    })
    assert resp.status_code in (200, 204), resp.text
    assert _ingredient(recipe_id)["label"] == "mozzarella"


def test__add_line__carries_a_preferred_buy(api):
    item = _new_item()
    pb = _preferred_buy(item, "Bega Tasty")
    lst = requests.post(f"{BASE}/shopping-lists", json={"name": f"IngChoice {uuid4().hex[:8]}"}).json()
    list_id = lst["shopping_list_id"]

    resp = requests.post(f"{BASE}/shopping-lists/{list_id}/lines",
                         json={"stock_item_id": item, "preferred_buy_id": pb})
    assert resp.status_code == 200, resp.text

    line = requests.get(f"{BASE}/shopping-lists/{list_id}").json()["lines"][0]
    assert line["preferred_buy_id"] == pb
