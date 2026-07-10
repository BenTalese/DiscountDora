"""FU-519 — shared CRUD assertions for the small taxonomy routers.

Cuisines / categories / dietary tags / tools / stock groups all share the
same generic router shape (`manage_cuisines.py` is the reference): bare-list
GET, create-with-duplicate-guard, rename-with-duplicate-guard, delete that
reports how many referencing rows were touched. One helper here per contract
leg; each surface keeps its own `test_<surface>_router.py` for
discoverability and passes a :class:`TaxonomySurface` describing its quirks
(id key, DTO keys, duplicate message, update/delete response shape).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from uuid import uuid4

import requests

from tests.e2e.dora_api._error_assertions import domain_err, validation_err
from tests.support import assert_problem, is_valid_uuid


@dataclass(frozen=True)
class TaxonomySurface:
    base: str                              # full collection URL
    id_key: str                            # e.g. "cuisine_id"
    entity: str                            # 404 detail entity name, e.g. "Cuisine"
    dto_keys: frozenset                    # keys of one list-DTO row
    duplicate_message: Callable[[str], str]
    create_body: Callable[[str], dict] = staticmethod(lambda name: {"name": name})
    update_status: int = 200               # stock groups return 204 on rename
    delete_count_key: str = "recipes_affected"  # stock groups: items_affected


def unique_name(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def get_all(surface: TaxonomySurface) -> list[dict]:
    resp = requests.get(surface.base)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Bare list, not the {items,total,page,limit} envelope — pinned.
    assert isinstance(body, list), f"expected bare list, got {type(body).__name__}"
    return body


def create(surface: TaxonomySurface, name: str) -> str:
    resp = requests.post(surface.base, json=surface.create_body(name))
    assert resp.status_code == 201, resp.text
    new_id = resp.json()[surface.id_key]
    assert is_valid_uuid(new_id)
    assert f"filter={surface.id_key}:eq:{new_id}" in resp.headers["location"]
    return new_id


def assert_created_row_shape(surface: TaxonomySurface, new_id: str, name: str) -> dict:
    row = next(r for r in get_all(surface) if r[surface.id_key] == new_id)
    assert set(row.keys()) == set(surface.dto_keys)
    assert row["name"] == name
    return row


def assert_duplicate_create_is_422(surface: TaxonomySurface, name: str) -> None:
    # Uniqueness is case-insensitive — SWAPCASE must still collide.
    resp = requests.post(surface.base, json=surface.create_body(name.swapcase()))
    body = assert_problem(resp, 422, title="Business rule violation.")
    assert body["errors"] == {
        "": [domain_err(surface.duplicate_message(name.swapcase()))],
    }


def assert_empty_create_is_400(surface: TaxonomySurface) -> None:
    resp = requests.post(surface.base, json={})
    body = assert_problem(resp, 400, field="name", title="Malformed request.")
    assert body["errors"]["name"] == [validation_err("missing", "Field required")]


def rename(surface: TaxonomySurface, entity_id: str, new_name: str) -> None:
    resp = requests.patch(f"{surface.base}/{entity_id}", json={"name": new_name})
    assert resp.status_code == surface.update_status, resp.text
    row = next(r for r in get_all(surface) if r[surface.id_key] == entity_id)
    assert row["name"] == new_name


def assert_rename_to_duplicate_is_422(
    surface: TaxonomySurface, entity_id: str, taken_name: str,
) -> None:
    resp = requests.patch(f"{surface.base}/{entity_id}", json={"name": taken_name})
    body = assert_problem(resp, 422, title="Business rule violation.")
    assert body["errors"] == {"": [domain_err(surface.duplicate_message(taken_name))]}


def assert_unknown_id_is_404(surface: TaxonomySurface) -> None:
    missing_id = uuid4()
    detail = f"{surface.entity} with the ID '{missing_id}' was not found."
    assert_problem(
        requests.patch(f"{surface.base}/{missing_id}", json={"name": "Ghost"}),
        404, detail=detail,
    )
    assert_problem(requests.delete(f"{surface.base}/{missing_id}"), 404, detail=detail)


def delete(surface: TaxonomySurface, entity_id: str, *, expect_affected: int = 0) -> None:
    resp = requests.delete(f"{surface.base}/{entity_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {surface.delete_count_key: expect_affected}
    assert entity_id not in {r[surface.id_key] for r in get_all(surface)}
