"""FU-351 — the "Draft my shop" server contract on `POST /shopping-lists/auto-generate`
(verify-campaign Batch: Dashboard).

The dashboard card leans on two create-new-path behaviours the unit-of-work
test doesn't cover:

* **Zero candidates defers list creation.** A call whose sources yield nothing
  answers `nothing_to_add: true` with a null `shopping_list_id` and leaves NO
  phantom list behind — the card renders an honest "Nothing to draft yet."
  toast instead of stranding a "Weekly shop · <date>" shell in the sidebar.
* **The explicit `name` is honoured** on the created list (the card sends
  "Weekly shop · <weekday> <day> <month>" instead of the generic "Auto N ·
  <date>" default).
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"
AUTO = f"{LISTS}/auto-generate"


def _list_ids() -> set[str]:
    resp = requests.get(LISTS)
    assert resp.status_code == 200, resp.text
    return {l["shopping_list_id"] for l in resp.json()}


def test__auto_generate__zero_candidates_on_create_new__no_phantom_list(api):
    before = _list_ids()

    # A meal-plan week far in the future has no entries, and every other
    # source is off → zero candidates.
    resp = requests.post(AUTO, json={
        "name": f"FU-351 phantom {uuid4().hex[:8]}",
        "sources": {"meal_plan_week": "2030-01-01"},
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["nothing_to_add"] is True
    assert body["shopping_list_id"] is None
    assert body["added_count"] == 0

    # The list collection is untouched — creation was deferred, not rolled back.
    assert _list_ids() == before


def test__auto_generate__create_new_honours_the_explicit_name(api):
    stock_level_id = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    item_resp = requests.post(f"{BASE}/stock-items", json={
        "name": f"FU-351 named {uuid4().hex[:8]}",
        "stock_level_id": stock_level_id,
        "is_flagged": True,
    })
    assert item_resp.status_code == 201, item_resp.text
    stock_item_id = item_resp.json()["stock_item_id"]

    list_name = f"Weekly shop · test {uuid4().hex[:8]}"
    generated_list_id = None
    try:
        resp = requests.post(AUTO, json={
            "name": list_name,
            "sources": {"flagged": True},
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert not body["nothing_to_add"], body
        generated_list_id = body["shopping_list_id"]

        detail = requests.get(f"{LISTS}/{generated_list_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["display_name"] == list_name
    finally:
        if generated_list_id:
            requests.delete(f"{LISTS}/{generated_list_id}")
        requests.patch(f"{BASE}/stock-items/{stock_item_id}", json={"is_flagged": False})
        requests.delete(f"{BASE}/stock-items/{stock_item_id}")
