"""FU-512 — `POST /shopping-lists/<id>/copy` is a unit of work.

Pre-FU-512 committed twice (new list, then copied lines). Now: one commit.
Happy-path only — no reachable failure surface exists between the two former
commits (the loop is over already-loaded source lines).
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"


def _a_stock_item_id() -> str:
    return requests.get(f"{BASE}/stock-items?limit=1").json()["items"][0]["stock_item_id"]


def test__copy_shopping_list__all_valid__commits_target_and_lines_together(api):
    source_id = requests.post(LISTS, json={"name": f"FU-512 src {uuid4()}"}).json()["shopping_list_id"]
    stock_item_id = _a_stock_item_id()
    add_resp = requests.post(f"{LISTS}/{source_id}/lines", json={
        "stock_item_id": stock_item_id,
        "quantity": 2,
    })
    assert add_resp.status_code in (200, 201), add_resp.text

    copy_id = None
    try:
        copy_resp = requests.post(f"{LISTS}/{source_id}/copy", json={
            "name": f"FU-512 copy {uuid4()}", "include": "all",
        })
        assert copy_resp.status_code == 200, copy_resp.text
        copy_id = copy_resp.json()["shopping_list_id"]

        detail = requests.get(f"{LISTS}/{copy_id}")
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["lines"]) == 1
    finally:
        if copy_id:
            requests.delete(f"{LISTS}/{copy_id}")
        requests.delete(f"{LISTS}/{source_id}")
