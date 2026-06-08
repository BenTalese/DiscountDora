"""P6-01 Chunk 7 — planned_shop_date persistence + DTO exposure.

A list can be created with an ISO planned_shop_date, the value round-trips through
the summary + detail DTOs, PATCH can change it, and PATCH with explicit `null`
clears it.
"""
import requests

SHOPPING_LISTS = "http://localhost:5170/api/shopping-lists"


def _create(payload: dict) -> str:
    resp = requests.post(SHOPPING_LISTS, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["shopping_list_id"]


def _detail(list_id: str) -> dict:
    resp = requests.get(f"{SHOPPING_LISTS}/{list_id}")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _patch(list_id: str, payload: dict) -> None:
    resp = requests.patch(f"{SHOPPING_LISTS}/{list_id}", json=payload)
    assert resp.status_code == 204, resp.text


def _cleanup(list_id: str) -> None:
    requests.delete(f"{SHOPPING_LISTS}/{list_id}")


def test_create_with_planned_shop_date_roundtrips_through_dtos():
    list_id = _create({"name": "Chunk 7 create", "planned_shop_date": "2026-07-01"})
    try:
        detail = _detail(list_id)
        assert detail["planned_shop_date"] == "2026-07-01"
        # Summary DTO also exposes it.
        all_lists = requests.get(SHOPPING_LISTS).json()
        summary = next(s for s in all_lists if s["shopping_list_id"] == list_id)
        assert summary["planned_shop_date"] == "2026-07-01"
    finally:
        _cleanup(list_id)


def test_create_without_planned_shop_date_defaults_null():
    list_id = _create({"name": "Chunk 7 no date"})
    try:
        detail = _detail(list_id)
        assert detail["planned_shop_date"] is None
    finally:
        _cleanup(list_id)


def test_patch_sets_and_clears_planned_shop_date():
    list_id = _create({"name": "Chunk 7 patch"})
    try:
        assert _detail(list_id)["planned_shop_date"] is None

        _patch(list_id, {"planned_shop_date": "2026-08-15"})
        assert _detail(list_id)["planned_shop_date"] == "2026-08-15"

        # Explicit null clears.
        _patch(list_id, {"planned_shop_date": None})
        assert _detail(list_id)["planned_shop_date"] is None
    finally:
        _cleanup(list_id)


def test_patch_without_planned_shop_date_field_does_not_touch_it():
    # Set a date, then PATCH something else — the date must survive.
    list_id = _create({"name": "Chunk 7 preserve", "planned_shop_date": "2026-09-01"})
    try:
        _patch(list_id, {"name": "Chunk 7 renamed"})
        detail = _detail(list_id)
        assert detail["name"] == "Chunk 7 renamed"
        assert detail["planned_shop_date"] == "2026-09-01"
    finally:
        _cleanup(list_id)
