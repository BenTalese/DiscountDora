"""P6-01 Chunk 1 — shopping-list lifecycle (status model + server-owned undo).

Covers the new single `status` field (draft / shopping / done) that replaced the
old is_archived / is_in_progress boolean pair, and the server-owned finish/reopen
that reverses a finish from the server's own `finish_snapshot` (no client snapshot
posted to /unfinish).
"""
from uuid import uuid4

import pytest
import requests

from dora_api.features.stock_items.create_stock_item import \
    CreateStockItemRequest

SHOPPING_LISTS = "http://localhost:5170/api/shopping-lists"
STOCK_ITEMS = "http://localhost:5170/api/stock-items"
STOCK_LEVELS = "http://localhost:5170/api/stock-levels"


#region ---------------- fixtures ----------------

@pytest.fixture
def levels_by_sequence():
    # /stock-levels is paginated ({items, total, …}); key the seeded levels by
    # ordinal sequence (0 Well-Stocked … 3 Out of Stock) so the test never
    # depends on display names.
    levels = requests.get(STOCK_LEVELS).json()["items"]
    return {l["sequence"]: l["stock_level_id"] for l in levels}


def _create_list(name: str) -> str:
    resp = requests.post(SHOPPING_LISTS, json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _detail(list_id: str) -> dict:
    resp = requests.get(f"{SHOPPING_LISTS}/{list_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _item_level(item_id: str) -> str:
    item = requests.get(f"{STOCK_ITEMS}?filter=stock_item_id:eq:{item_id}").json()["items"][0]
    return item["stock_level_id"]

#endregion fixtures


def test__create_shopping_list__defaults_to_draft_status(api):
    list_id = _create_list(f"Lifecycle draft {uuid4()}")
    detail = _detail(list_id)
    assert detail["status"] == "draft"
    # Legacy flags are gone from the DTO entirely.
    assert "is_archived" not in detail
    assert "is_in_progress" not in detail


def test__start__transitions_status__and_stop_is_removed(api):
    list_id = _create_list(f"Lifecycle start {uuid4()}")

    assert requests.post(f"{SHOPPING_LISTS}/{list_id}/start").status_code == 204
    assert _detail(list_id)["status"] == "shopping"

    # UX-v2: no pause — /stop was deleted with the shop-mode merge. The
    # lifecycle is start -> finish (-> reopen).
    assert requests.post(f"{SHOPPING_LISTS}/{list_id}/stop").status_code == 404


def test__update_status__invalid_value_is_rejected(api):
    list_id = _create_list(f"Lifecycle bad status {uuid4()}")
    resp = requests.patch(f"{SHOPPING_LISTS}/{list_id}", json={"status": "bogus"})
    assert resp.status_code in (400, 422), resp.text
    # Status unchanged.
    assert _detail(list_id)["status"] == "draft"


def test__summaries__expose_status_not_legacy_flags(api):
    _create_list(f"Lifecycle summary {uuid4()}")
    summaries = requests.get(SHOPPING_LISTS).json()
    assert summaries, "expected at least one shopping list"
    for s in summaries:
        assert "status" in s
        assert s["status"] in ("draft", "shopping", "done")
        assert "is_archived" not in s
        assert "is_in_progress" not in s


def test__finish_then_reopen__restores_level_server_side(api, levels_by_sequence):
    out_of_stock = levels_by_sequence[3]
    well_stocked = levels_by_sequence[0]

    # An item that starts Out of Stock so finish's restock is a visible change.
    item_name = f"Reopen-probe-{uuid4()}"
    create = requests.post(STOCK_ITEMS, json=CreateStockItemRequest(
        name=item_name,
        stock_level_id=out_of_stock,
    ).model_dump(mode="json"))
    assert create.status_code == 201, create.text
    item_id = create.json()["stock_item_id"]
    assert _item_level(item_id) == out_of_stock

    # Put it on a list and tick it.
    list_id = _create_list(f"Lifecycle finish {uuid4()}")
    add = requests.post(f"{SHOPPING_LISTS}/{list_id}/lines", json={"stock_item_id": item_id})
    assert add.status_code == 200, add.text
    line_id = add.json()["line_id"]
    tick = requests.patch(
        f"{SHOPPING_LISTS}/{list_id}/lines/{line_id}", json={"is_ticked": True}
    )
    assert tick.status_code in (200, 204), tick.text

    # Finish: list -> done, ticked item restocked to Well-Stocked.
    finish = requests.post(f"{SHOPPING_LISTS}/{list_id}/finish")
    assert finish.status_code == 200, finish.text
    assert _detail(list_id)["status"] == "done"
    assert _item_level(item_id) == well_stocked

    # Reopen with NO request body — the server reverses the finish from its own
    # finish_snapshot. List -> draft, item level restored to Out of Stock.
    reopen = requests.post(f"{SHOPPING_LISTS}/{list_id}/unfinish")
    assert reopen.status_code == 204, reopen.text
    assert _detail(list_id)["status"] == "draft"
    assert _item_level(item_id) == out_of_stock
