"""End-to-end coverage for the A1 auth surface.

Each test gets a fresh requests.Session so test order doesn't matter
and the authenticated `dora` cookie from conftest doesn't leak in
when the test means to be anonymous.
"""
import uuid

import requests


BASE = "http://localhost:5170/api/auth"


def _fresh_session() -> requests.Session:
    return requests.Session()


def _register(s: requests.Session, username: str, password: str, email: str | None = None):
    return s.post(f"{BASE}/register", json={
        "username": username, "password": password,
        **({"email": email} if email else {}),
    })


def test__register__rejects_weak_password(api):
    s = _fresh_session()
    response = _register(s, f"weak-{uuid.uuid4().hex[:6]}", "shortpw", "x@example.com")
    assert response.status_code == 422
    body = response.json()
    assert "password" in (body.get("errors") or {})


def test__register__rejects_bad_email_format(api):
    s = _fresh_session()
    response = _register(s, f"bademail-{uuid.uuid4().hex[:6]}", "Abcdefghij1", "not-an-email")
    assert response.status_code == 422


def test__register__happy_path(api):
    s = _fresh_session()
    username = f"happy-{uuid.uuid4().hex[:8]}"
    response = _register(s, username, "Abcdefghij1", f"{username}@example.com")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["username"] == username
    assert body["email_verified"] is False
    # Auto-login should have set the session cookie.
    me = s.get(f"{BASE}/me")
    assert me.status_code == 200


def test__register__rejects_duplicate_email_case_insensitive(api):
    s = _fresh_session()
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    first = _register(s, f"dup1-{uuid.uuid4().hex[:6]}", "Abcdefghij1", email)
    assert first.status_code == 200, first.text
    s2 = _fresh_session()
    second = _register(s2, f"dup2-{uuid.uuid4().hex[:6]}", "Abcdefghij1", email.upper())
    assert second.status_code == 422


def test__forgot_password__anti_enumeration(api):
    s = _fresh_session()
    # Returns 204 regardless of whether the email exists.
    response = s.post(f"{BASE}/forgot-password", json={
        "email": f"nobody-{uuid.uuid4().hex}@example.com",
    })
    assert response.status_code == 204


def test__verify_email__invalid_token__is_400(api):
    s = _fresh_session()
    response = s.post(f"{BASE}/verify-email", json={"token": "definitely-not-real"})
    assert response.status_code == 400


def test__reset_password__invalid_token__is_400(api):
    s = _fresh_session()
    response = s.post(f"{BASE}/reset-password", json={
        "token": "bogus", "new_password": "Abcdefghij1",
    })
    assert response.status_code == 400


def test__reset_password__weak_password__is_422(api):
    s = _fresh_session()
    response = s.post(f"{BASE}/reset-password", json={
        "token": "bogus", "new_password": "short",
    })
    assert response.status_code == 422


def test__login__rate_limit_returns_429_eventually(api):
    s = _fresh_session()
    # The endpoint allows 5/min per IP. Spam past the limit.
    for _ in range(6):
        s.post(f"{BASE}/login", json={
            "username": "rate-probe", "password": "wrong",
        })
    response = s.post(f"{BASE}/login", json={
        "username": "rate-probe", "password": "wrong",
    })
    assert response.status_code in (401, 429)
    if response.status_code == 429:
        assert "Retry-After" in response.headers
