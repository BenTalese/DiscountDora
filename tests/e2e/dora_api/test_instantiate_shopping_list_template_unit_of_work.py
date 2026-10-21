"""FU-512 — `POST /shopping-list-templates/<id>/instantiate` is a unit of work.

Pre-FU-512 committed twice (new list, then lines) and skipped the second
commit when every template line pointed at a deleted stock item. Now: one
commit; a template with no persistable lines still creates an empty list.
"""
from uuid import uuid4

import requests

BASE = "http://localhost:5170/api"
SL_TEMPLATES = f"{BASE}/shopping-list-templates"
LISTS = f"{BASE}/shopping-lists"


def _a_stock_item_id() -> str:
    return requests.get(f"{BASE}/stock-items?limit=1").json()["items"][0]["stock_item_id"]


def test__instantiate_shopping_list_template__all_valid__commits_list_and_lines_together(api):
    template_id = requests.post(SL_TEMPLATES, json={
        "name": f"FU-512 SL tpl {uuid4()}",
        "lines": [{"stock_item_id": _a_stock_item_id(), "quantity": 1}],
    }).json()["template_id"]

    list_id = None
    try:
        resp = requests.post(f"{SL_TEMPLATES}/{template_id}/instantiate", json={
            "name": f"FU-512 instantiate {uuid4()}",
        })
        assert resp.status_code == 200, resp.text
        assert resp.json()["line_count"] == 1
        list_id = resp.json()["shopping_list_id"]

        detail = requests.get(f"{LISTS}/{list_id}")
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["lines"]) == 1
    finally:
        if list_id:
            requests.delete(f"{LISTS}/{list_id}")
        requests.delete(f"{SL_TEMPLATES}/{template_id}")
