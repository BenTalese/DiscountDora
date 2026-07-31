"""FU-573 — the by-stock-item remove endpoint reports whether it actually
removed a line.

The endpoint is idempotent: removing an item that isn't on the list is a no-op
success. Previously it returned 204 (no body), so a "remove from all open lists"
fan-out counted every 2xx as a removal and over-reported ("Removed from 3 lists"
for an item on 1). It now returns `{"removed": bool}` so callers count real
removals. This pins that contract.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
LISTS = f"{BASE}/shopping-lists"


def _stock_level_id(sequence: int = 0) -> str:
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    return next(l["stock_level_id"] for l in levels if l["sequence"] == sequence)


def _make_draft() -> str:
    resp = requests.post(LISTS, json={"name": f"RemoveByItem-{uuid4().hex[:8]}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _remove_by_item(list_id: str, stock_item_id: str) -> requests.Response:
    return requests.delete(f"{LISTS}/{list_id}/lines/by-stock-item/{stock_item_id}")


def test__remove_by_stock_item__reports_removed_true_then_false(api):
    list_id = _make_draft()
    sid = make_stock_item(stock_level_id=_stock_level_id(),
                          name=f"RemoveMe-{uuid4().hex[:8]}")["stock_item_id"]

    add = requests.post(f"{LISTS}/{list_id}/lines", json={"stock_item_id": sid})
    assert add.status_code == 200, add.text

    first = _remove_by_item(list_id, sid)
    assert first.status_code == 200, first.text
    assert first.json()["removed"] is True

    # Idempotent no-op the second time: still 200, but nothing was removed.
    second = _remove_by_item(list_id, sid)
    assert second.status_code == 200, second.text
    assert second.json()["removed"] is False


def test__remove_by_stock_item__never_on_list_reports_false(api):
    list_id = _make_draft()
    sid = make_stock_item(stock_level_id=_stock_level_id(),
                          name=f"NeverAdded-{uuid4().hex[:8]}")["stock_item_id"]
    resp = _remove_by_item(list_id, sid)
    assert resp.status_code == 200, resp.text
    assert resp.json()["removed"] is False


def test__remove_by_stock_item__unknown_list_is_404(api):
    sid = make_stock_item(stock_level_id=_stock_level_id(),
                          name=f"NoList-{uuid4().hex[:8]}")["stock_item_id"]
    resp = _remove_by_item(str(uuid4()), sid)
    assert resp.status_code == 404, resp.text
