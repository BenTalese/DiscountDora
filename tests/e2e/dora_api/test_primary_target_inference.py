"""P6-01 Chunk 2 — DRAFT-count primary-target inference.

Verifies the rules behind POST /api/shopping-lists/primary/lines now that the
stored `is_primary` flag is gone:

  - 0 draft lists  -> result="no_draft"
  - 1 draft list   -> result="added" (silent quick-add)
  - 2+ draft lists -> result="ambiguous" with candidates, and the client can
                      disambiguate by sending `shopping_list_id`

Plus a couple of sanity checks: SHOPPING/DONE lists never count as candidates,
and the membership endpoint surfaces `quick_add_target_list_id` mirroring the
same rule.
"""
from uuid import uuid4

import pytest
import requests

from dora_api.features.stock_items.create_stock_item import \
    CreateStockItemRequest

SHOPPING_LISTS = "http://localhost:5170/api/shopping-lists"
STOCK_ITEMS = "http://localhost:5170/api/stock-items"
STOCK_LEVELS = "http://localhost:5170/api/stock-levels"
QUICK_ADD = f"{SHOPPING_LISTS}/primary/lines"
MEMBERSHIP = f"{SHOPPING_LISTS}/membership"


#region ---------------- fixtures ----------------

@pytest.fixture
def levels_by_sequence():
    levels = requests.get(STOCK_LEVELS).json()["items"]
    return {l["sequence"]: l["stock_level_id"] for l in levels}


@pytest.fixture
def fresh_state(api):
    # Archive every existing active list so each test starts with a known
    # draft-count. The seed leaves several active lists around; rather than
    # deleting them we move them to status=done (they don't affect resolver).
    summaries = requests.get(SHOPPING_LISTS).json()
    for s in summaries:
        if s["status"] != "done":
            r = requests.patch(
                f"{SHOPPING_LISTS}/{s['shopping_list_id']}", json={"status": "done"}
            )
            assert r.status_code == 204, r.text
    yield


def _create_list(name: str) -> str:
    resp = requests.post(SHOPPING_LISTS, json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _create_stock_item(name: str, level_id: str) -> str:
    resp = requests.post(STOCK_ITEMS, json=CreateStockItemRequest(
        name=name, stock_level_id=level_id,
    ).model_dump(mode="json"))
    assert resp.status_code == 201, resp.text
    return resp.json()["stock_item_id"]

#endregion fixtures


def test__quick_add__zero_drafts__returns_no_draft(
    fresh_state, levels_by_sequence
):
    item_id = _create_stock_item(
        f"no-drafts-{uuid4()}", levels_by_sequence[0]
    )
    resp = requests.post(QUICK_ADD, json={"stock_item_id": item_id})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"result": "no_draft"}


def test__quick_add__single_draft__adds_silently(
    fresh_state, levels_by_sequence
):
    list_id = _create_list(f"single-draft-{uuid4()}")
    item_id = _create_stock_item(
        f"single-draft-item-{uuid4()}", levels_by_sequence[0]
    )
    resp = requests.post(QUICK_ADD, json={"stock_item_id": item_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["result"] == "added"
    assert body["shopping_list_id"] == list_id
    assert body["already_on_list"] is False


def test__quick_add__two_drafts__returns_ambiguous_with_candidates(
    fresh_state, levels_by_sequence
):
    a = _create_list(f"draft-a-{uuid4()}")
    b = _create_list(f"draft-b-{uuid4()}")
    item_id = _create_stock_item(
        f"two-drafts-item-{uuid4()}", levels_by_sequence[0]
    )

    resp = requests.post(QUICK_ADD, json={"stock_item_id": item_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["result"] == "ambiguous"
    ids = {c["shopping_list_id"] for c in body["candidates"]}
    assert ids == {a, b}

    # Disambiguate: client passes the chosen list_id.
    resp2 = requests.post(
        QUICK_ADD, json={"stock_item_id": item_id, "shopping_list_id": b}
    )
    assert resp2.status_code == 200, resp2.text
    added = resp2.json()
    assert added["result"] == "added"
    assert added["shopping_list_id"] == b


def test__quick_add__shopping_list_does_not_count_as_draft(
    fresh_state, levels_by_sequence
):
    # One DRAFT + one SHOPPING — resolver still sees a single DRAFT, so
    # quick-add lands silently on the draft. SHOPPING is for in-store ticking,
    # not the quick-add target.
    draft = _create_list(f"draft-{uuid4()}")
    shopping = _create_list(f"shopping-{uuid4()}")
    r = requests.post(f"{SHOPPING_LISTS}/{shopping}/start")
    assert r.status_code == 204, r.text

    item_id = _create_stock_item(
        f"draft-vs-shopping-{uuid4()}", levels_by_sequence[0]
    )
    resp = requests.post(QUICK_ADD, json={"stock_item_id": item_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["result"] == "added"
    assert body["shopping_list_id"] == draft


def test__quick_add__hint_invalid_for_non_draft(
    fresh_state, levels_by_sequence
):
    # If the client sends a hint that no longer points to a draft (e.g. the
    # remembered sessionStorage pick after the user finished that list), the
    # server rejects with a business-rule violation so the client can clear
    # the pick and re-prompt.
    list_id = _create_list(f"finished-{uuid4()}")
    r = requests.patch(f"{SHOPPING_LISTS}/{list_id}", json={"status": "done"})
    assert r.status_code == 204, r.text

    item_id = _create_stock_item(
        f"hint-invalid-{uuid4()}", levels_by_sequence[0]
    )
    resp = requests.post(
        QUICK_ADD, json={"stock_item_id": item_id, "shopping_list_id": list_id}
    )
    assert resp.status_code in (400, 422), resp.text


def test__membership__quick_add_target_mirrors_inference(
    fresh_state, levels_by_sequence
):
    # Zero drafts -> no target.
    resp = requests.get(MEMBERSHIP).json()
    assert resp["quick_add_target_list_id"] is None

    # One draft -> that draft is the target.
    list_id = _create_list(f"membership-draft-{uuid4()}")
    resp = requests.get(MEMBERSHIP).json()
    assert resp["quick_add_target_list_id"] == list_id

    # Two drafts -> ambiguous, so the target is cleared.
    _create_list(f"membership-second-{uuid4()}")
    resp = requests.get(MEMBERSHIP).json()
    assert resp["quick_add_target_list_id"] is None


def test__create_request__rejects_legacy_make_primary(fresh_state):
    # Belt-and-braces: extra=forbid on the create DTO must reject the old
    # `make_primary` field so a stale client surfaces a clear error rather
    # than silently doing nothing.
    resp = requests.post(SHOPPING_LISTS, json={"name": f"x-{uuid4()}", "make_primary": True})
    assert resp.status_code in (400, 422), resp.text
