"""RD-18 (FU-407) — shopping-list line exposes `has_substitutes`.

The line-detail DTO carries a server-derived flag so the SPA can disable the
"Swap with substitute" affordance up front instead of surfacing it as a
dead-end. A line whose stock item has a recorded substitute reads True; one
without reads False.
"""
import uuid

import requests

BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"
SHOPPING_LISTS = f"{BASE}/shopping-lists"


def _new_item() -> str:
    level = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    return requests.post(STOCK_ITEMS, json={
        "name": f"sub-{uuid.uuid4().hex[:8]}", "stock_level_id": level,
    }).json()["stock_item_id"]


def _line_for(list_id: str, item_id: str) -> dict:
    lines = requests.get(f"{SHOPPING_LISTS}/{list_id}").json()["lines"]
    return next(l for l in lines if l["stock_item_id"] == item_id)


def test__line_has_substitutes__true_only_when_a_substitute_is_linked(api):
    with_sub = _new_item()
    the_sub = _new_item()
    without_sub = _new_item()

    # Link with_sub <-> the_sub as substitutes.
    linked = requests.post(
        f"{STOCK_ITEMS}/{with_sub}/substitutes", json={"substitute_id": the_sub},
    )
    assert linked.status_code in (200, 201, 204), linked.text

    list_id = requests.post(
        SHOPPING_LISTS, json={"name": f"subs-{uuid.uuid4().hex[:8]}"}
    ).json()["shopping_list_id"]
    for item in (with_sub, without_sub):
        assert requests.post(
            f"{SHOPPING_LISTS}/{list_id}/lines", json={"stock_item_id": item},
        ).status_code in (200, 201)

    assert _line_for(list_id, with_sub)["has_substitutes"] is True
    assert _line_for(list_id, without_sub)["has_substitutes"] is False
    # The substitute item itself, if listed, also reads True (undirected pair).
    assert requests.post(
        f"{SHOPPING_LISTS}/{list_id}/lines", json={"stock_item_id": the_sub},
    ).status_code in (200, 201)
    assert _line_for(list_id, the_sub)["has_substitutes"] is True
