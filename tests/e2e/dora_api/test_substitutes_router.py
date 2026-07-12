"""FU-519 tail — the stock-item substitutes HTTP surface.

`test_substitute_metadata.py` (FU-034) owns notes/ratio round-trips,
direction-aware ratio inversion and the metadata validation matrix.
This suite covers what that one doesn't:

  * canonical undirected-pair storage — adding the same pair from the
    OTHER side is a no-op, not a second row
  * the self-substitute and missing-entity error paths on all three verbs
  * unit-alias canonicalisation ("tablespoons" persists as "tbsp")
  * DELETE round-trip from either side + idempotency (second delete 404s)
  * PATCH on a pair that was never linked → 404

Substitutes have no standalone router — the endpoints live under
/api/stock-items/<id>/substitutes (the old /substitutes graph page was
CUT; the per-item list is the kept surface). The deals feature
(dora_api/features/deals/) exposes no HTTP routes at all — deal_quality
is a pure helper consumed by other handlers — so there is nothing to
cover there.
"""
from uuid import uuid4

import requests

from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"


def _uniq(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _stock_level_id() -> str:
    return requests.get(f"{BASE}/stock-levels").json()["items"][0]["stock_level_id"]


def _make_item(prefix: str) -> str:
    item = make_stock_item(stock_level_id=_stock_level_id(), name=_uniq(prefix))
    return item["stock_item_id"]


def _substitutes_of(stock_item_id: str) -> list[dict]:
    resp = requests.get(f"{BASE}/stock-items/{stock_item_id}/detail")
    assert resp.status_code == 200, resp.text
    return resp.json()["substitutes"]


def _link(a: str, b: str, **metadata) -> None:
    resp = requests.post(
        f"{BASE}/stock-items/{a}/substitutes",
        json={"substitute_id": b, **metadata},
    )
    assert resp.status_code == 204, resp.text


# ── canonical pair storage ───────────────────────────────────────────────

def test__add_substitute__same_pair_from_the_other_side__no_duplicate_row(api):
    a = _make_item("canon-a")
    b = _make_item("canon-b")
    _link(a, b)

    # Adding B→A after A→B is reported as success (idempotent
    # already-linked, 204) and does NOT create a second row.
    resp = requests.post(
        f"{BASE}/stock-items/{b}/substitutes", json={"substitute_id": a}
    )
    assert resp.status_code == 204, resp.text

    assert [s["stock_item_id"] for s in _substitutes_of(a)] == [b]
    assert [s["stock_item_id"] for s in _substitutes_of(b)] == [a]


def test__add_substitute__pair_visible_from_both_sides(api):
    a = _make_item("both-a")
    b = _make_item("both-b")
    _link(a, b)

    side_a = _substitutes_of(a)
    side_b = _substitutes_of(b)
    assert len(side_a) == 1 and side_a[0]["stock_item_id"] == b
    assert len(side_b) == 1 and side_b[0]["stock_item_id"] == a
    # The DTO also carries the substitute's current level for the picker.
    assert side_a[0]["name"]
    assert side_a[0]["stock_level_id"] is not None


def test__add_substitute__unit_aliases_canonicalised_on_persist(api):
    # "tablespoons" is an alias in the UNIT_TABLE — the persisted (and
    # served) form is the canonical "tbsp".
    a = _make_item("alias-a")
    b = _make_item("alias-b")
    _link(
        a, b,
        ratio_quantity_in=1, ratio_unit_in="tablespoons",
        ratio_quantity_out=2, ratio_unit_out="teaspoon",
    )
    sub = _substitutes_of(a)[0]
    assert sub["ratio_unit_in"] == "tbsp"
    assert sub["ratio_unit_out"] == "tsp"


# ── add: error paths ─────────────────────────────────────────────────────

def test__add_substitute__self__rejected_422(api):
    a = _make_item("self-a")
    resp = requests.post(
        f"{BASE}/stock-items/{a}/substitutes", json={"substitute_id": a}
    )
    assert resp.status_code == 422, resp.text
    assert "own substitute" in resp.text


def test__add_substitute__nonexistent_substitute__is_clean_422(api):
    a = _make_item("ghost-sub-a")
    resp = requests.post(
        f"{BASE}/stock-items/{a}/substitutes", json={"substitute_id": str(uuid4())}
    )
    assert resp.status_code == 422, resp.text
    assert "substitute_id" in resp.json()["errors"]


def test__add_substitute__nonexistent_stock_item__404(api):
    b = _make_item("ghost-item-b")
    resp = requests.post(
        f"{BASE}/stock-items/{uuid4()}/substitutes", json={"substitute_id": b}
    )
    assert resp.status_code == 404, resp.text


def test__add_substitute__missing_substitute_id__rejected_400(api):
    a = _make_item("nobody-a")
    resp = requests.post(f"{BASE}/stock-items/{a}/substitutes", json={})
    assert resp.status_code == 400, resp.text
    assert "substitute_id" in resp.json()["errors"]


# ── update: error paths (happy paths live in test_substitute_metadata) ──

def test__update_substitute__pair_never_linked__404(api):
    a = _make_item("nolink-a")
    b = _make_item("nolink-b")
    resp = requests.patch(
        f"{BASE}/stock-items/{a}/substitutes/{b}", json={"notes": "hi"}
    )
    assert resp.status_code == 404, resp.text


def test__update_substitute__self_pair__404(api):
    a = _make_item("selfpatch-a")
    resp = requests.patch(
        f"{BASE}/stock-items/{a}/substitutes/{a}", json={"notes": "hi"}
    )
    assert resp.status_code == 404, resp.text


def test__update_substitute__unknown_unit__rejected_422(api):
    a = _make_item("badunit-a")
    b = _make_item("badunit-b")
    _link(a, b)
    resp = requests.patch(f"{BASE}/stock-items/{a}/substitutes/{b}", json={
        "ratio_quantity_in": 1, "ratio_unit_in": "galactic-cubit",
        "ratio_quantity_out": 1, "ratio_unit_out": "tsp",
    })
    assert resp.status_code == 422, resp.text
    assert "unknown unit" in resp.text.lower()


def test__update_substitute__from_the_b_side__persists_reoriented_ratio(api):
    # Editing from the OTHER side of the pair: the body is expressed from
    # B's perspective, and each side's detail view keeps showing the
    # ratio from its own perspective.
    a = _make_item("bside-a")
    b = _make_item("bside-b")
    _link(a, b)

    resp = requests.patch(f"{BASE}/stock-items/{b}/substitutes/{a}", json={
        "ratio_quantity_in": 3, "ratio_unit_in": "cup",
        "ratio_quantity_out": 1, "ratio_unit_out": "cup",
    })
    assert resp.status_code == 204, resp.text

    from_b = _substitutes_of(b)[0]
    assert (from_b["ratio_quantity_in"], from_b["ratio_quantity_out"]) == (3, 1)
    from_a = _substitutes_of(a)[0]
    assert (from_a["ratio_quantity_in"], from_a["ratio_quantity_out"]) == (1, 3)


# ── delete ───────────────────────────────────────────────────────────────

def test__remove_substitute__from_the_other_side__removes_the_pair(api):
    a = _make_item("del-a")
    b = _make_item("del-b")
    _link(a, b)

    # Delete via the B side even though the link was added from A —
    # canonical storage means direction doesn't matter.
    resp = requests.delete(f"{BASE}/stock-items/{b}/substitutes/{a}")
    assert resp.status_code == 204, resp.text
    assert _substitutes_of(a) == []
    assert _substitutes_of(b) == []


def test__remove_substitute__twice__second_is_404(api):
    a = _make_item("del2-a")
    b = _make_item("del2-b")
    _link(a, b)
    assert requests.delete(f"{BASE}/stock-items/{a}/substitutes/{b}").status_code == 204
    resp = requests.delete(f"{BASE}/stock-items/{a}/substitutes/{b}")
    assert resp.status_code == 404, resp.text


def test__remove_substitute__nonexistent_stock_item__404(api):
    b = _make_item("delghost-b")
    resp = requests.delete(f"{BASE}/stock-items/{uuid4()}/substitutes/{b}")
    assert resp.status_code == 404, resp.text


def test__remove_substitute__self_pair__404(api):
    a = _make_item("delself-a")
    resp = requests.delete(f"{BASE}/stock-items/{a}/substitutes/{a}")
    assert resp.status_code == 404, resp.text


def test__delete_stock_item__clears_the_pair_for_the_survivor(api):
    # Referential integrity: deleting one side of a pair must not leave
    # a dangling substitute row on the survivor's detail page.
    a = _make_item("cascade-a")
    b = _make_item("cascade-b")
    _link(a, b)
    assert requests.delete(f"{BASE}/stock-items/{b}").status_code == 204
    assert _substitutes_of(a) == []
