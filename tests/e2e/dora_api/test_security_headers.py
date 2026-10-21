"""Security response headers (FU-459) — DORA_VERIFY Cross-cutting L1535/L1542.

Every response must carry the app-wide security headers (set in
`middleware.after_app_request`), including error responses. A regression that
dropped `X-Frame-Options` / the CSP would be silent otherwise — nothing else
exercises them.
"""
import requests

BASE = "http://localhost:5170/api"

_SIMPLE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer-when-downgrade",
}


def _assert_security_headers(resp) -> None:
    for name, value in _SIMPLE_HEADERS.items():
        assert resp.headers.get(name) == value, f"{name}: {resp.headers.get(name)!r}"
    csp = resp.headers.get("Content-Security-Policy", "")
    # Key directives (assert substrings, not the exact joined string, so a
    # harmless reorder doesn't break the pin).
    for directive in (
        "default-src 'self'",
        "frame-ancestors 'none'",       # clickjacking defence, CSP-native
        "img-src 'self' data: blob: https:",  # base64 blobs + uploads + ext images
        "base-uri 'self'",
        "form-action 'self'",
    ):
        assert directive in csp, f"CSP missing {directive!r}: {csp!r}"


def test__security_headers__present_on_a_200(api):
    resp = requests.get(f"{BASE}/stock-levels")
    assert resp.status_code == 200, resp.text
    _assert_security_headers(resp)


def test__security_headers__present_on_a_404(api):
    # Error responses must be covered too — the after_request hook runs for
    # every response, not just successful ones.
    resp = requests.get(f"{BASE}/this-route-does-not-exist")
    assert resp.status_code == 404
    _assert_security_headers(resp)


def test__security_headers__present_on_a_domain_422(api):
    # A validation/business-rule error path (goes through the error handlers)
    # still carries the headers.
    resp = requests.post(f"{BASE}/recipes", json={})  # missing required name
    assert resp.status_code == 400
    _assert_security_headers(resp)
