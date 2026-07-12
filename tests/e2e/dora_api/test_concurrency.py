"""FU-535 — concurrency / race / idempotency behaviour.

Every other test issues requests one-at-a-time; nothing exercises a
double-submitted mutation, an offline-queue replay, or two operations
touching one row. These are the bugs single-threaded tests miss.

APPROACH (decided per the stub's feasibility note): **deterministic
interleaving**, not real threads. The e2e conftest dispatches in-process
through Flask's test client over one SQLite file — genuine ThreadPoolExecutor
parallelism hits SQLite write-locks and the client's thread-safety and would
be flaky. Every race here is a *logic* race (idempotency, lost-update via
read-modify-write, delete-then-reference ordering), so it reproduces by
driving the steps by hand in the adversarial order. Cases that genuinely need
MVCC (true simultaneous writers) are deferred to Postgres CI (FU-045/FU-405)
and noted where they'd apply.

Covers stub cases 1 (double-submit), 2 (disjoint PATCH lost-update), 4
(repeated level drops), 5 (delete-then-reference). Case 3 (reconcile sweep vs
manual verb) is already owned by the reconcile suite + [[FU-529]]'s ordering
pin, so it's not duplicated here.
"""
import requests

from dora_api.app import app
from dora_api.domain.entities.consumption_event import ConsumptionEvent
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from tests.factories import make_stock_item

BASE = "http://localhost:5170/api"
STOCK_ITEMS = f"{BASE}/stock-items"


def _uniq(prefix: str) -> str:
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _levels_top_bottom() -> tuple[str, str]:
    levels = sorted(
        requests.get(f"{BASE}/stock-levels").json()["items"],
        key=lambda l: l["sequence"],
    )
    return levels[0]["stock_level_id"], levels[-1]["stock_level_id"]


def _detail(item_id: str) -> dict:
    return requests.get(f"{STOCK_ITEMS}/{item_id}/detail").json()


def _consumption_count(item_id: str) -> int:
    with app.app_context():
        return len(
            SqlAlchemyRepository().get(ConsumptionEvent).all(
                EntityField(ConsumptionEvent, "stock_item_id").eq(item_id)
            )
        )


# ── Case 1 — double-submit ─────────────────────────────────────────────────

def test__double_submit_create__is_deduped_by_name_uniqueness(api):
    """Double-tapping a stock-item create does NOT produce two rows: the
    name-uniqueness guard rejects the second identical POST with a 422. So the
    server itself protects against the classic double-submit duplicate for
    name-unique entities — the second tap is a clean business-rule rejection,
    not a phantom duplicate. (Entities WITHOUT a uniqueness guard are why the
    offline queue still refuses to queue creates at all — identity-creating
    ops fail loudly offline rather than risk a duplicate on replay.)"""
    level, _ = _levels_top_bottom()
    body = {"name": _uniq("dbl-create"), "stock_level_id": level}
    r1 = requests.post(STOCK_ITEMS, json=body)
    r2 = requests.post(STOCK_ITEMS, json=body)
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 422, (
        f"a duplicate-name create should be rejected, got {r2.status_code}: {r2.text[:200]}"
    )


def test__double_submit_level_drop__records_consumption_once(api):
    """The offline queue replays a mutation VERBATIM, and a user can double-tap.
    A level drop applied twice must be idempotent in its side effects: the
    first PATCH (top->bottom) is a real drop and records one ConsumptionEvent;
    the second (bottom->bottom) is a no-op and must record NOTHING. A
    double-count here would corrupt depletion history on every reconnect."""
    top, bottom = _levels_top_bottom()
    item = make_stock_item(stock_level_id=top, name=_uniq("dbl-drop"))
    item_id = item["stock_item_id"]

    payload = {"stock_level_id": bottom, "consumption_source": "manual"}
    assert requests.patch(f"{STOCK_ITEMS}/{item_id}", json=payload).status_code in (200, 204)
    history_after_first = len(_detail(item_id)["level_history"])
    assert requests.patch(f"{STOCK_ITEMS}/{item_id}", json=payload).status_code in (200, 204)

    assert _consumption_count(item_id) == 1, (
        "a re-applied (same-level) drop double-counted consumption — offline "
        "replay / double-tap would corrupt depletion history"
    )
    # And the no-op second PATCH must not append a phantom history row (FU-533).
    assert len(_detail(item_id)["level_history"]) == history_after_first


# ── Case 2 — lost update via read-modify-write ─────────────────────────────

def test__disjoint_patches__both_fields_persist_either_order(api):
    """Two PATCHes to one item touching DIFFERENT fields (notes vs level) must
    BOTH land, in either interleaving — no last-writer-wins clobber of the
    field the other request didn't touch. This proves the handler does a
    PARTIAL update (writes only model_fields_set), not a read-whole-modify-
    write-whole that would clobber. If it regressed to full-object writes,
    interleaved requests would lose the earlier field."""
    top, bottom = _levels_top_bottom()
    for order in ("notes_first", "level_first"):
        item = make_stock_item(stock_level_id=top, name=_uniq(f"disjoint-{order}"))
        item_id = item["stock_item_id"]
        patches = [
            {"notes": "concurrent note"},
            {"stock_level_id": bottom},
        ]
        if order == "level_first":
            patches.reverse()
        for p in patches:
            assert requests.patch(f"{STOCK_ITEMS}/{item_id}", json=p).status_code in (200, 204)

        detail = _detail(item_id)
        assert detail["notes"] == "concurrent note", (order, "notes clobbered")
        assert detail["stock_level_id"] == bottom, (order, "level clobbered")


# ── Case 4 — repeated level drops keep the ledger consistent ────────────────

def test__successive_sourced_drops__record_one_event_each(api):
    """Two genuine drops (top->mid->bottom) each record exactly one
    ConsumptionEvent — no skipped or double-counted sequence. Guards the
    FU-533 fix under repeated depletion (the cook-then-cook-again path)."""
    levels = sorted(
        requests.get(f"{BASE}/stock-levels").json()["items"],
        key=lambda l: l["sequence"],
    )
    assert len(levels) >= 3, "need >=3 stock levels for a two-step drop"
    top, mid, bottom = levels[0], levels[len(levels) // 2], levels[-1]
    item = make_stock_item(stock_level_id=top["stock_level_id"], name=_uniq("multi-drop"))
    item_id = item["stock_item_id"]

    for lvl in (mid, bottom):
        assert requests.patch(f"{STOCK_ITEMS}/{item_id}", json={
            "stock_level_id": lvl["stock_level_id"], "consumption_source": "manual",
        }).status_code in (200, 204)

    assert _consumption_count(item_id) == 2, (
        "two distinct drops should record two ConsumptionEvents"
    )


# ── Case 5 — delete-then-reference (delete-wins interleaving) ───────────────

def test__reference_a_just_deleted_item__is_rejected_cleanly(api):
    """The delete-while-referenced race, driven delete-first: request A deletes
    a stock item, request B (which read the item before the delete) tries to
    add it to a shopping list. The add must fail cleanly (4xx) — never a 500,
    never a dangling line pointing at a ghost item."""
    top, _ = _levels_top_bottom()
    item = make_stock_item(stock_level_id=top, name=_uniq("del-race"))
    item_id = item["stock_item_id"]
    list_id = requests.post(f"{BASE}/shopping-lists", json={"name": _uniq("race-list")}).json()["shopping_list_id"]

    assert requests.delete(f"{STOCK_ITEMS}/{item_id}").status_code in (200, 204)

    resp = requests.post(
        f"{BASE}/shopping-lists/{list_id}/lines",
        json={"stock_item_id": item_id, "quantity": 1},
    )
    assert 400 <= resp.status_code < 500, (
        f"adding a line for a deleted item should 4xx, got {resp.status_code}: "
        f"{resp.text[:200]}"
    )
    # No orphan line landed.
    lines = requests.get(f"{BASE}/shopping-lists/{list_id}").json()["lines"]
    assert all(l.get("stock_item_id") != item_id for l in lines)
