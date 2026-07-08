"""FU-512 — `POST /shopping-lists/auto-generate` is a unit of work.

Pre-FU-512 the create-new path committed twice (new list, then lines). Now:
one commit at the end of the handler. `_create_list()` relies on SQLAlchemy
autoflush of the pending ShoppingList row when the immediate downstream
`.all()` on ShoppingListLine executes — so FK visibility for the lines is
preserved.

Happy-path only: no reachable failure surface between the two former commits.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"
AUTO = f"{LISTS}/auto-generate"


def test__auto_generate__flagged_source__commits_list_and_lines_together(api):
    # Seed a flagged stock item that will be picked up by the flagged source.
    stock_level_id = requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]
    name = f"FU-512 flagged {uuid4().hex[:8]}"
    create = requests.post(f"{BASE}/stock-items", json={
        "name": name,
        "stock_level_id": stock_level_id,
        "is_flagged": True,
    })
    assert create.status_code in (200, 201), create.text
    stock_item_id = create.json().get("stock_item_id") or create.json().get("id")

    generated_list_id = None
    try:
        resp = requests.post(AUTO, json={
            "name": f"FU-512 auto {uuid4()}",
            "sources": {"flagged": True},
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert not body.get("nothing_to_add"), body
        assert body.get("added_count", 0) >= 1
        generated_list_id = body["shopping_list_id"]

        detail = requests.get(f"{LISTS}/{generated_list_id}")
        assert detail.status_code == 200, detail.text
        assert any(l.get("stock_item_id") == stock_item_id for l in detail.json()["lines"]), \
            "the flagged stock item should have landed on the generated list"
    finally:
        if generated_list_id:
            requests.delete(f"{LISTS}/{generated_list_id}")
        # unflag + delete the seed stock item so other tests aren't polluted
        requests.patch(f"{BASE}/stock-items/{stock_item_id}", json={"is_flagged": False})
        requests.delete(f"{BASE}/stock-items/{stock_item_id}")
