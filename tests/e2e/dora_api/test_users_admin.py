"""Users admin — Add / Delete behaviour (FU-461).

DORA_VERIFY Settings L1047–L1061. `test_route_auth_enforcement.py` pins the
admin gate on these endpoints and `test_patch_semantics.py` covers the PATCH
guards; this closes the create-validation and delete-guard behaviour:

* create → 200 + one-time password + the user is listed;
* create with a taken username / taken email / malformed email → 422;
* delete your own account → 403 (self-delete refused);
* delete another user → 204 and they leave the list;
* delete a non-existent user → 404.

The delete-last-admin guard is symmetric with the PATCH-demotion guard already
pinned in test_patch_semantics; it's hard to reach here (self-delete precedence +
the single seeded admin), so it stays owner-walk.
"""
from uuid import uuid4

import requests

from tests.support import assert_problem

BASE = "http://localhost:5170/api"
USERS = f"{BASE}/users"


def _uniq(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _create(**body) -> requests.Response:
    return requests.post(USERS, json={"username": _uniq("admin-user"), **body})


def _me() -> dict:
    return requests.get(f"{BASE}/auth/me").json()


def _row(user_id: str) -> dict | None:
    items = requests.get(USERS, params={"filter": f"user_id:eq:{user_id}"}).json()["items"]
    return items[0] if items else None


def test__admin_create_user__returns_one_time_password_and_lists_the_user(api):
    resp = _create(email=f"{_uniq('mail')}@example.com", is_admin=True)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"]
    # The one-time password travels in the body (not retrievable later).
    assert isinstance(body["new_password"], str) and len(body["new_password"]) >= 12
    row = _row(body["user_id"])
    assert row is not None
    assert row["is_admin"] is True


def test__admin_create_user__taken_username__rejected_422(api):
    first = _create()
    assert first.status_code == 200, first.text
    taken = _row(first.json()["user_id"])["username"]
    resp = requests.post(USERS, json={"username": taken})
    assert_problem(resp, 422)
    assert "already taken" in resp.text.lower()


def test__admin_create_user__taken_email__rejected_422(api):
    email = f"{_uniq('mail')}@example.com"
    first = _create(email=email)
    assert first.status_code == 200, first.text
    resp = _create(email=email)
    assert_problem(resp, 422)
    assert "already registered" in resp.text.lower()


def test__admin_create_user__malformed_email__rejected_422(api):
    resp = _create(email="nope")
    body = assert_problem(resp, 422, field="email")
    assert "valid email" in resp.text.lower()


def test__admin_delete_user__self__is_forbidden_403(api):
    me = _me()
    resp = requests.delete(f"{USERS}/{me['user_id']}")
    assert resp.status_code == 403, resp.text
    assert "your own account" in resp.text.lower()
    # Still there.
    assert _row(me["user_id"]) is not None


def test__admin_delete_user__another_user__removed(api):
    created = _create()
    user_id = created.json()["user_id"]
    assert _row(user_id) is not None
    resp = requests.delete(f"{USERS}/{user_id}")
    assert resp.status_code == 204, resp.text
    assert _row(user_id) is None


def test__admin_delete_user__unknown__404(api):
    resp = requests.delete(f"{USERS}/{uuid4()}")
    assert resp.status_code == 404, resp.text
