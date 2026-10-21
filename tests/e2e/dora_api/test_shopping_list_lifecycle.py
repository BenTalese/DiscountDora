"""P6-01 Chunk 1 — shopping-list lifecycle (status model).

Covers the single `status` field (draft / shopping / done) that replaced the
old is_archived / is_in_progress boolean pair. Once a list is done, it's done —
FU-163 retired Reopen / /unfinish along with the rest of the app-wide undo
posture.
"""
from uuid import uuid4

import requests

SHOPPING_LISTS = "http://localhost:5170/api/shopping-lists"


def _create_list(name: str) -> str:
    resp = requests.post(SHOPPING_LISTS, json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _detail(list_id: str) -> dict:
    resp = requests.get(f"{SHOPPING_LISTS}/{list_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


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
    # lifecycle is start -> finish; once done, it's done (no /unfinish either).
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


def test__unfinish_endpoint_is_removed(api):
    # undo posture retired — /unfinish (Reopen) no longer exists.
    list_id = _create_list(f"Lifecycle no-reopen {uuid4()}")
    assert requests.post(f"{SHOPPING_LISTS}/{list_id}/start").status_code == 204
    assert requests.post(f"{SHOPPING_LISTS}/{list_id}/finish").status_code == 200
    assert _detail(list_id)["status"] == "done"
    assert requests.post(f"{SHOPPING_LISTS}/{list_id}/unfinish").status_code == 404
