"""FU-512 — `POST /shopping-list-templates/from-list/<id>` is a unit of work.

Pre-FU-512 committed twice (template row, then snapshot lines). Now: one
commit.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
SL_TEMPLATES = f"{BASE}/shopping-list-templates"
LISTS = f"{BASE}/shopping-lists"


def _a_stock_item_id() -> str:
    return requests.get(f"{BASE}/stock-items?limit=1").json()["items"][0]["stock_item_id"]


def test__snapshot_shopping_list__all_valid__commits_template_and_lines_together(api):
    src_id = requests.post(LISTS, json={"name": f"FU-512 src {uuid4()}"}).json()["shopping_list_id"]
    add_resp = requests.post(f"{LISTS}/{src_id}/lines", json={
        "stock_item_id": _a_stock_item_id(),
        "quantity": 3,
    })
    assert add_resp.status_code in (200, 201), add_resp.text

    template_id = None
    try:
        resp = requests.post(f"{SL_TEMPLATES}/from-list/{src_id}", json={
            "name": f"FU-512 snapshot {uuid4()}",
            "include_ticked": True,
        })
        assert resp.status_code in (200, 201), resp.text
        template_id = resp.json()["template_id"]
        assert resp.json()["line_count"] == 1

        detail = requests.get(f"{SL_TEMPLATES}/{template_id}")
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["lines"]) == 1
    finally:
        if template_id:
            requests.delete(f"{SL_TEMPLATES}/{template_id}")
        requests.delete(f"{LISTS}/{src_id}")
