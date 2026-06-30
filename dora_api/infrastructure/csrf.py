"""FU-197 — CSRF double-submit-cookie defence.

Model
-----
Every response that doesn't already carry the `dora_csrf` cookie gets a
fresh, random one set in `after_app_request`. The cookie is **not**
HttpOnly — the SPA must be able to read it from `document.cookie` and
echo it as the `X-CSRF-Token` header on every mutating request.

Every mutating request (`POST/PATCH/PUT/DELETE`) under `/api/*` whose
endpoint is *not* listed in `PUBLIC_ENDPOINTS` (login/register/etc.) and
*not* the bearer-authenticated ingestion endpoint must carry the header,
and its value must constant-time match the cookie. Mismatch → 403.

Why double-submit and not synchroniser tokens
---------------------------------------------
A1.5: the SPA already has same-origin script context on the auth domain,
so reading a non-HttpOnly cookie is fine and avoids a server-side token
store. The attacker on `evil.example` cannot read the cookie thanks to
the Same-Origin Policy and so can't forge the header — even if a
SameSite=Lax cookie leaks on a same-site sub-domain.

Bootstrap timing
----------------
On a cold-load the SPA hits a GET (`/auth/bootstrap-required` or
`/auth/me`) before any POST. That GET seeds the cookie, so the
follow-up POST/PATCH has both halves of the double-submit. Public
endpoints (login/register/forgot/reset/verify/bootstrap_admin) are
exempt so a brand-new client without a cookie can still authenticate.
"""

import hmac
import secrets

from flask import Request, Response, request


CSRF_COOKIE_NAME = "dora_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
_CSRF_BYTES = 32  # 64 hex chars; matches Flask's secret-key tier.

_MUTATING_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})


def issue_token() -> str:
    """Fresh random token for the cookie. URL-safe hex."""
    return secrets.token_hex(_CSRF_BYTES)


def request_token(req: Request | None = None) -> str | None:
    """Return the CSRF cookie value on the current (or given) request, or
    None if the client didn't send one."""
    r = req if req is not None else request
    value = r.cookies.get(CSRF_COOKIE_NAME)
    return value if value else None


def header_token(req: Request | None = None) -> str | None:
    """Return the `X-CSRF-Token` header value, or None if absent."""
    r = req if req is not None else request
    value = r.headers.get(CSRF_HEADER_NAME)
    return value if value else None


def request_is_mutating() -> bool:
    return request.method.upper() in _MUTATING_METHODS


def request_under_api() -> bool:
    return request.path.startswith("/api/")


def csrf_check_passed() -> bool:
    """True when the request carries a matching cookie + header.
    `hmac.compare_digest` keeps the comparison constant-time."""
    cookie = request_token()
    header = header_token()
    if not cookie or not header:
        return False
    return hmac.compare_digest(cookie, header)


def attach_cookie(response: Response, token: str, *, secure: bool) -> None:
    """Set the CSRF cookie. SameSite=Lax mirrors the session cookie; we
    rely on the header echo (not SameSite alone) for the actual defence,
    so this is just to keep behaviour consistent with `dora_session`."""
    response.set_cookie(
        CSRF_COOKIE_NAME,
        token,
        secure=secure,
        httponly=False,  # SPA must read it.
        samesite="Lax",
        path="/",
    )


def ensure_cookie(response: Response, *, secure: bool) -> None:
    """If the incoming request didn't carry a CSRF cookie, mint one and
    attach it to the response so the next request has both halves of the
    double-submit pair."""
    if request_token() is not None:
        return
    attach_cookie(response, issue_token(), secure=secure)


def clear_cookie(response: Response) -> None:
    """Drop the CSRF cookie (paired with `session.clear()` on logout)."""
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
