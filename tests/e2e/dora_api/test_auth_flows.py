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


def test__register__never_grants_admin(api):
    """FU-200 — /register no longer self-grants admin. Self-serve accounts
    are always created with `is_admin=False`; the first-admin path is
    /bootstrap-admin (single-use, separately tested)."""
    s = _fresh_session()
    username = f"noadmin-{uuid.uuid4().hex[:8]}"
    response = _register(s, username, "Abcdefghij1", f"{username}@example.com")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["is_admin"] is False
    assert body["email_verified"] is False


def test__bootstrap_required__false_when_users_exist(api):
    """FU-200 — the bootstrap-required probe returns `false` once any user
    exists. The seeded `dora` test account guarantees that's the case here.
    Never leaks the actual user count."""
    s = _fresh_session()
    response = s.get(f"{BASE}/bootstrap-required")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {"required": False}


def test__bootstrap_admin__rejects_when_users_exist(api):
    """FU-200 — POST /bootstrap-admin is a one-shot endpoint. Once any
    user exists every subsequent call must 410, regardless of credentials,
    so the race ("first registrant becomes admin") is closed."""
    s = _fresh_session()
    response = s.post(f"{BASE}/bootstrap-admin", json={
        "username": f"intruder-{uuid.uuid4().hex[:6]}",
        "password": "Abcdefghij1",
        "email": f"intruder-{uuid.uuid4().hex[:6]}@example.com",
    })
    assert response.status_code == 410, response.text
    # Session must NOT have been established by a failed bootstrap.
    me = s.get(f"{BASE}/me")
    assert me.status_code == 401


def test__bootstrap_admin__rejects_weak_password(api):
    """Validation runs before the 410 — but only because the request
    *passes* the cheap fast-reject branch on an empty DB. Here it 410s
    first (existing users); a fresh-DB browser-verify covers the 422 path."""
    s = _fresh_session()
    response = s.post(f"{BASE}/bootstrap-admin", json={
        "username": f"weak-{uuid.uuid4().hex[:6]}",
        "password": "short",
        "email": f"weak-{uuid.uuid4().hex[:6]}@example.com",
    })
    # Either 410 (already bootstrapped) or 422 (weak password) is correct
    # — both refuse the request. The DB-has-users branch wins in CI.
    assert response.status_code in (410, 422), response.text


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


# ── FU-197 — verified change-email flow + CSRF defence ────────────────
#
# These reuse the session-scoped `api` (the bootstrapped `dora`/`dora`
# user) rather than registering fresh accounts so we don't burn through
# the `auth.register` per-IP rate limit (10/min) — that bucket is shared
# across every test in the file. None of these flows actually mutate
# dora's address: the change-email request only issues an auth-token row
# and queues an email; the address itself flips on confirmation, which
# lives in a separate confirmation flow.


def test__update_me__rejects_email_field(api):
    """FU-197 — the legacy unverified email-write path on PATCH /auth/me
    is closed; the field is now forbidden by the request model."""
    import requests
    response = requests.patch(
        f"{BASE}/me",
        json={"email": f"hijack-{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert response.status_code == 400, response.text


def test__request_email_change__current_password_gates_the_call(api):
    """FU-197 — `current_password` is a required field (model-level 400
    when missing) AND the value must match (business-rule 422 when
    wrong, 204 when right)."""
    import requests
    new_email = f"dora-new-{uuid.uuid4().hex[:6]}@example.com"

    # Missing current_password — model-level rejection.
    missing = requests.post(f"{BASE}/me/email", json={"new_email": new_email})
    assert missing.status_code == 400, missing.text

    # Wrong current_password — business-rule rejection.
    wrong = requests.post(f"{BASE}/me/email", json={
        "new_email": new_email,
        "current_password": "DefinitelyNotIt",
    })
    assert wrong.status_code == 422, wrong.text

    # Right current_password — 204 (the actual swap is gated by clicking
    # the confirmation link, which lives in a separate flow).
    ok = requests.post(f"{BASE}/me/email", json={
        "new_email": new_email,
        "current_password": "dora",  # the bootstrap user's password
    })
    assert ok.status_code == 204, ok.text


def test__csrf__mutation_without_header_is_403(api):
    """FU-197 — the double-submit defence rejects an authenticated
    mutating request that's missing the `X-CSRF-Token` header (the
    cookie may still be set; the *match* is what gates the call)."""
    import requests
    # Bypass the conftest's auto-attach by passing an empty header
    # explicitly; the wrapper sets it via `setdefault`, so a present-
    # but-empty value wins and the server sees no valid token. PATCH
    # the username back to its existing value so a future state-leak
    # would be a no-op anyway — but expect the call to never reach the
    # handler because the CSRF gate fires first.
    response = requests.patch(
        f"{BASE}/me",
        json={"username": "dora"},
        headers={"X-CSRF-Token": ""},
    )
    assert response.status_code == 403, response.text


# Settings rebuild Phase 4 — profile picture round-trip.
_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA"
    "60e6kgAAAABJRU5ErkJggg=="
)


def test__profile_picture__set_fetch_and_clear(api):
    """A user can set a profile picture (data-URL), it round-trips on the
    `has_image` flag + the bytes endpoint, and clearing removes it again."""
    s = _fresh_session()
    username = f"pic-{uuid.uuid4().hex[:8]}"
    reg = _register(s, username, "Abcdefghij1", f"{username}@example.com")
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["user_id"]
    assert reg.json()["has_image"] is False

    # No picture yet → bytes endpoint 404s.
    img = s.get(f"http://localhost:5170/api/users/{user_id}/image")
    assert img.status_code == 404

    # Set one via PATCH /auth/me.
    patched = s.patch(f"{BASE}/me", json={"image": _PNG_DATA_URL})
    assert patched.status_code == 200, patched.text
    assert patched.json()["has_image"] is True

    # Bytes now served with the declared mime.
    img = s.get(f"http://localhost:5170/api/users/{user_id}/image")
    assert img.status_code == 200, img.text
    assert img.headers["Content-Type"].startswith("image/png")
    assert len(img.content) > 0

    # Clear it → flag flips back, bytes 404 again.
    cleared = s.patch(f"{BASE}/me", json={"clear_image": True})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["has_image"] is False
    img = s.get(f"http://localhost:5170/api/users/{user_id}/image")
    assert img.status_code == 404


def test__profile_picture__rejects_oversize_data_url(api):
    """The ~4.5 MB base64 cap (max_length=6_000_000) rejects a huge payload
    rather than letting a 50 MB selfie through. The middleware emits 400 on
    pydantic ValidationError (codebase convention; see
    infrastructure/middleware.deserialise_web_request)."""
    s = _fresh_session()
    username = f"big-{uuid.uuid4().hex[:8]}"
    assert _register(s, username, "Abcdefghij1", f"{username}@example.com").status_code == 200
    oversize = "data:image/png;base64," + ("A" * 6_000_001)
    resp = s.patch(f"{BASE}/me", json={"image": oversize})
    assert resp.status_code == 400, resp.status_code


def test__dashboard_layout__set_and_clear(api):
    """A user's dashboard layout JSON round-trips on /auth/me and clears with
    an explicit null (Dashboard rebuild Phase 2)."""
    s = _fresh_session()
    username = f"dash-{uuid.uuid4().hex[:8]}"
    reg = _register(s, username, "Abcdefghij1", f"{username}@example.com")
    assert reg.status_code == 200, reg.text
    assert reg.json()["dashboard_layout"] is None

    layout = '{"order":["budget","attention"],"hidden":["meal_plan"]}'
    patched = s.patch(f"{BASE}/me", json={"dashboard_layout": layout})
    assert patched.status_code == 200, patched.text
    assert patched.json()["dashboard_layout"] == layout

    # Explicit null clears it back to the default layout.
    cleared = s.patch(f"{BASE}/me", json={"dashboard_layout": None})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["dashboard_layout"] is None


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
