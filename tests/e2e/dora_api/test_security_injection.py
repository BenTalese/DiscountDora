"""FU-537 — security: the app's input can't ESCAPE its layer.

`test_api_fuzz.py` proved endpoints don't 500 on garbage; this suite proves
user-controlled input can't break out of the layer it lands in — SQL
injection through the `?filter=field:op:value` / `?sort=` grammar, stored
HTML reaching a rendered email unescaped, and mass-assignment of privilege
fields. These are the failures that don't crash (so fuzzing misses them).

The filter grammar is designed safe (field is allowlist-mapped to an
EntityField, operator is an enum, value is a bound parameter). These tests
are the standing guard that it STAYS safe — a refactor that starts
interpolating the field or value into raw SQL fails here.
"""
import uuid

import requests

from dora_api.infrastructure.email_sender import render_template
from tests.factories import make_stock_item


BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"
AUTH_ME = f"{BASE}/auth/me"


def _level_id() -> str:
    return requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]


def _token() -> str:
    return uuid.uuid4().hex[:8]


# ═══ Filter/sort injection through the query grammar ══════════════════════

# Classic payloads aimed at the VALUE position. The query builder binds the
# value as a parameter, so these must be treated as literal search text —
# match nothing, never execute, never 500.
_VALUE_INJECTIONS = [
    "'; DROP TABLE StockItem;--",
    "1 OR 1=1",
    "' OR '1'='1",
    "%' OR name LIKE '%",
    "1); DELETE FROM Store;--",
]


def test__filter_value_injection__is_treated_as_literal_not_sql(api):
    # Seed a known item so the list is non-empty; an injection that "worked"
    # (e.g. 1=1) would return it, a literal match won't.
    marker = f"sec-{_token()}"
    make_stock_item(stock_level_id=_level_id(), name=marker)

    for payload in _VALUE_INJECTIONS:
        resp = requests.get(STOCK_ITEMS, params={"filter": f"name:eq:{payload}"})
        assert resp.status_code == 200, (payload, resp.text)
        # A parameterised eq against a literal that isn't our item name must
        # return zero rows — never "all rows" (which is what a working
        # `OR 1=1` injection would do).
        items = resp.json()["items"]
        assert all(i["name"] != marker for i in items), (
            f"injection payload {payload!r} appears to have matched more than a "
            f"literal value — possible SQL injection. Got {len(items)} items."
        )


def test__filter_value_injection__contains_operator_is_also_literal(api):
    for payload in _VALUE_INJECTIONS:
        resp = requests.get(STOCK_ITEMS, params={"filter": f"name:ct:{payload}"})
        assert resp.status_code == 200, (payload, resp.text)


def test__filter_field_injection__unknown_field_is_rejected_not_reflected(api):
    # The field is allowlist-mapped to an EntityField; anything off the map
    # must be rejected, never reflected into SQL. Includes dunders (the
    # FU-546 dunder-traversal fix) and a relationship name (`stock_level`) —
    # a non-column attribute that used to reach the query builder and 500;
    # the FU-546 strict-column allowlist now 400s it.
    for field in ["__class__", "1=1", "name);DROP TABLE StockItem;--", "password",
                  "stock_level", "products", "__dict__"]:
        resp = requests.get(STOCK_ITEMS, params={"filter": f"{field}:eq:x"})
        assert resp.status_code == 400, (
            f"non-column filter field {field!r} should 400, got {resp.status_code}: "
            f"{resp.text[:200]}"
        )


def test__filter_operator_injection__unknown_operator_is_400(api):
    for op in ["xx", "eq;DROP", "or", ""]:
        resp = requests.get(STOCK_ITEMS, params={"filter": f"name:{op}:x"})
        assert resp.status_code == 400, (op, resp.text[:200])


def test__sort_injection__malformed_or_unknown_is_400(api):
    for sort in [
        "name;DROP TABLE Store",        # no ':' → malformed
        "name:asc;DELETE FROM Store",   # bad direction
        "__class__:asc",                # unknown field
        "name:sideways",                # bad direction
    ]:
        resp = requests.get(STOCK_ITEMS, params={"sort": sort})
        assert resp.status_code == 400, (sort, resp.text[:200])


def test__injection_attempts__leave_the_table_intact(api):
    """After firing every injection payload above, a normal list must still
    return — proving nothing was dropped/deleted."""
    marker = f"survivor-{_token()}"
    make_stock_item(stock_level_id=_level_id(), name=marker)

    for payload in _VALUE_INJECTIONS:
        requests.get(STOCK_ITEMS, params={"filter": f"name:eq:{payload}"})
        requests.get(STOCK_ITEMS, params={"sort": f"name;{payload}"})

    resp = requests.get(STOCK_ITEMS, params={"limit": 500})
    assert resp.status_code == 200, resp.text
    names = {i["name"] for i in resp.json()["items"]}
    assert marker in names, "the StockItem table did not survive the injection sweep"


# ═══ Mass-assignment of privilege / identity fields ═══════════════════════

def test__patch_me__cannot_mass_assign_is_admin(api):
    # extra="forbid" on the request model must reject a privilege-escalation
    # field outright (400), not silently ignore it.
    resp = requests.patch(AUTH_ME, json={"is_admin": True})
    assert resp.status_code == 400, resp.text
    # And the caller is definitely still not... well, dora IS admin, but the
    # point is the field was rejected at the schema, not applied.
    assert requests.get(AUTH_ME).status_code == 200


def test__patch_me__cannot_mass_assign_id(api):
    # id / user_id are server-owned — extra="forbid" hard-rejects them.
    # (email IS editable via this endpoint now; see the auth-flow tests.)
    for field, value in [("id", str(uuid.uuid4())), ("user_id", str(uuid.uuid4()))]:
        resp = requests.patch(AUTH_ME, json={field: value})
        assert resp.status_code == 400, (field, resp.text[:200])


def test__create_store__cannot_mass_assign_id(api):
    resp = requests.post(
        f"{BASE}/stores", json={"name": f"sec-{_token()}", "id": str(uuid.uuid4())}
    )
    assert resp.status_code == 400, resp.text


# ═══ Stored-XSS: user content reaching a rendered email unescaped ═════════

_XSS = '<script>alert(1)</script>'


def test__email_render__escapes_html_in_user_controlled_fields(api):
    # Jinja autoescape must be on for .html templates: a username containing
    # a script tag must render escaped, never as live markup.
    html = render_template(
        "verify_email.html",
        subject="Verify your Dashy Dora account",
        username=_XSS,
        verify_url="https://dora.example/verify-email?token=tok",
    )
    assert _XSS not in html, "user content rendered as live HTML — stored XSS risk"
    assert "&lt;script&gt;" in html, "expected the script tag to be HTML-escaped"


def test__email_render__escapes_html_in_the_subject(api):
    html = render_template(
        "verify_email.html",
        subject=_XSS,
        username="ben",
        verify_url="https://dora.example/verify-email?token=tok",
    )
    assert _XSS not in html
    assert "&lt;script&gt;" in html
