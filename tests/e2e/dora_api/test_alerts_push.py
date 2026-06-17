"""C-9.8 — web-push subscription endpoints + the push job.

`send_alerts_push` is driven directly (the scheduler is disabled in
test env). Pushes are captured via the `_send_push` test seam — no
real VAPID keys, no real Mozilla/FCM round-trip. The seam matches the
production `send_push(endpoint=, p256dh=, auth=, payload=)` signature.
"""
import uuid
from datetime import datetime, timezone
from uuid import UUID

import pytest
import requests

from dora_api.app import app
from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.domain.entities.push_subscription import PushSubscription
from dora_api.features.alerts.send_alerts_push import send_alerts_push
from dora_api.infrastructure.push_sender import PushGoneError
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

BASE = "http://localhost:5170/api"


@pytest.fixture(autouse=True)
def _cleanup_push_state():
    """Each test in this module leaves a fresh slate for the next:
    drop every PushSubscription row + any push-stamps on the user's
    interactions. Keeps tests independent without rebuilding the DB."""
    yield
    with app.app_context():
        repo = SqlAlchemyRepository()
        for sub in repo.get(PushSubscription).all():
            repo.remove(sub)
        for row in repo.get(AlertInteraction).all():
            if row.last_pushed_at is not None:
                row.last_pushed_at = None
        repo.save_changes()


def _me_user_id() -> UUID:
    me = requests.get(f"{BASE}/auth/me").json()
    return UUID(me["user_id"])


def _any_stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json().get("items") or []
    return levels[0]["stock_level_id"]


def _create_expired_item(name: str) -> str:
    resp = requests.post(
        f"{BASE}/stock-items",
        json={
            "name": name,
            "stock_level_id": _any_stock_level_id(),
            "expiry_date": "2020-01-01",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["stock_item_id"]


def _delete_item(item_id: str) -> None:
    resp = requests.delete(f"{BASE}/stock-items/{item_id}")
    assert resp.status_code in (200, 204), resp.text


def _subscribe(endpoint: str) -> None:
    resp = requests.post(
        f"{BASE}/alerts/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "test-p256dh-" + uuid.uuid4().hex,
                      "auth": "test-auth-" + uuid.uuid4().hex[:16]},
            "user_agent": "pytest/1.0",
        },
    )
    assert resp.status_code == 204, resp.text


def _captured_sender():
    """Captures `(endpoint, p256dh, auth, payload)` per call."""
    calls: list[dict] = []
    def _capture(**kwargs):
        calls.append(kwargs)
    return calls, _capture


def _subscriptions_for(user_id: UUID) -> list[PushSubscription]:
    with app.app_context():
        repo = SqlAlchemyRepository()
        return repo.get(PushSubscription).all(
            EntityField(PushSubscription, PushSubscription.Fields.USER_ID).eq(user_id)
        )


def _pushed_keys_for(user_id: UUID) -> set[str]:
    with app.app_context():
        repo = SqlAlchemyRepository()
        rows = repo.get(AlertInteraction).all(
            EntityField(AlertInteraction, AlertInteraction.Fields.USER_ID).eq(user_id)
        )
        return {r.alert_key for r in rows if r.last_pushed_at is not None}


_NOW = datetime(2026, 6, 17, 10, 0, tzinfo=timezone.utc)


# ── Endpoint tests ─────────────────────────────────────────────────────


def test__push_subscribe__creates_row_then_upserts(api):
    user_id = _me_user_id()
    endpoint = f"https://test.push/endpoint/{uuid.uuid4().hex}"
    _subscribe(endpoint)

    rows = _subscriptions_for(user_id)
    matching = [r for r in rows if r.endpoint == endpoint]
    assert len(matching) == 1, "subscribe should create exactly one row"

    # Re-subscribing the same endpoint upserts (no second row).
    _subscribe(endpoint)
    rows = _subscriptions_for(user_id)
    matching = [r for r in rows if r.endpoint == endpoint]
    assert len(matching) == 1, "re-subscribe of same endpoint should upsert"


def test__push_unsubscribe__removes_row_and_is_idempotent(api):
    user_id = _me_user_id()
    endpoint = f"https://test.push/endpoint/{uuid.uuid4().hex}"
    _subscribe(endpoint)
    assert any(r.endpoint == endpoint for r in _subscriptions_for(user_id))

    resp = requests.post(
        f"{BASE}/alerts/push/unsubscribe",
        json={"endpoint": endpoint},
    )
    assert resp.status_code == 204, resp.text
    assert not any(r.endpoint == endpoint for r in _subscriptions_for(user_id))

    # Idempotent — a second call against the same (gone) endpoint is a no-op.
    resp = requests.post(
        f"{BASE}/alerts/push/unsubscribe",
        json={"endpoint": endpoint},
    )
    assert resp.status_code == 204, resp.text


def test__push_vapid_public_key__returns_404_when_unconfigured(api):
    # In the test env DORA_VAPID_* env vars aren't set → the endpoint
    # advertises "channel not configured" via a 404, so the SPA renders
    # the toggle as disabled-with-caption (R-014).
    resp = requests.get(f"{BASE}/alerts/push/vapid-public-key")
    assert resp.status_code == 404, resp.text


# ── Job tests ──────────────────────────────────────────────────────────


def test__push_job__sends_actionable_alerts_to_all_subscribed_devices(api):
    user_id = _me_user_id()
    endpoint_a = f"https://test.push/device-a/{uuid.uuid4().hex}"
    endpoint_b = f"https://test.push/device-b/{uuid.uuid4().hex}"
    _subscribe(endpoint_a)
    _subscribe(endpoint_b)
    name = f"push-fanout-{uuid.uuid4().hex[:8]}"
    # An expired-back-in-2020 item also reads as out_of_stock at the
    # seed's first level, so it may produce multiple actionable alerts
    # for the same stock item. The fanout invariant is per-alert-per-
    # device; assert both devices saw the same set of alert_ids.
    _create_expired_item(name)

    calls, sender = _captured_sender()
    sent = send_alerts_push(now=_NOW, _send_push=sender)
    assert sent >= 2, calls

    matching = [c for c in calls if name in c["payload"]["body"]]
    by_endpoint: dict[str, set[str]] = {}
    for c in matching:
        by_endpoint.setdefault(c["endpoint"], set()).add(c["payload"]["alert_id"])

    assert endpoint_a in by_endpoint and endpoint_b in by_endpoint, (
        f"both devices should have received pushes; got endpoints {list(by_endpoint)}"
    )
    assert by_endpoint[endpoint_a] == by_endpoint[endpoint_b], (
        "both devices should see the same set of alert_ids for the new item; "
        f"a={by_endpoint[endpoint_a]} b={by_endpoint[endpoint_b]}"
    )
    # Stamped on the ledger so a second run won't re-push the same key.
    assert _pushed_keys_for(user_id)


def test__push_job__skips_fyi_tier_alerts(api):
    # `low_stock` defaults to FYI (PROPOSAL_ALERTS §5). The job filters
    # FYI items out — push is for things that need a response.
    user_id = _me_user_id()
    _subscribe(f"https://test.push/fyi-test/{uuid.uuid4().hex}")
    name = f"push-fyi-{uuid.uuid4().hex[:8]}"
    # Create at the low-stock level (sequence > 0 but < well-stocked).
    levels = requests.get(f"{BASE}/stock-levels").json()["items"]
    low_level = next((l for l in levels if "low" in l.get("name", "").lower()), levels[0])
    resp = requests.post(f"{BASE}/stock-items", json={
        "name": name,
        "stock_level_id": low_level["stock_level_id"],
    })
    assert resp.status_code in (200, 201), resp.text

    calls, sender = _captured_sender()
    send_alerts_push(now=_NOW, _send_push=sender)
    # The low-stock alert (if it fired) should NOT show up in pushed
    # bodies. Other actionable alerts from previous tests may push;
    # all we assert is that this specific FYI item isn't pushed.
    assert not any(name in c["payload"]["body"] for c in calls)


def test__push_job__dedups_until_alert_clears_and_refires(api):
    user_id = _me_user_id()
    _subscribe(f"https://test.push/dedup/{uuid.uuid4().hex}")
    name = f"push-dedup-{uuid.uuid4().hex[:8]}"
    item_id = _create_expired_item(name)

    calls, sender = _captured_sender()
    send_alerts_push(now=_NOW, _send_push=sender)
    first = len(calls)
    assert first >= 1

    # Second run with the same alert active → no fresh push for this key.
    send_alerts_push(now=_NOW, _send_push=sender)
    second = len(calls)
    if second > first:
        assert not any(
            name in c["payload"]["body"] for c in calls[first:]
        ), "deduped alert should not re-push"

    # Clearing the underlying item drops the key → cleanup pass clears
    # last_pushed_at. A fresh item with the same name produces a new
    # (different-id) key, so the new key has no prior interaction →
    # fresh push.
    _delete_item(item_id)
    send_alerts_push(now=_NOW, _send_push=sender)
    new_item = _create_expired_item(name)
    pre = len(calls)
    send_alerts_push(now=_NOW, _send_push=sender)
    assert len(calls) > pre, "re-fired condition should push fresh"
    _delete_item(new_item)


def test__push_job__prunes_gone_subscriptions(api):
    user_id = _me_user_id()
    gone_endpoint = f"https://test.push/dead/{uuid.uuid4().hex}"
    live_endpoint = f"https://test.push/live/{uuid.uuid4().hex}"
    _subscribe(gone_endpoint)
    _subscribe(live_endpoint)
    name = f"push-prune-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)

    def _selective_sender(**kwargs):
        if kwargs["endpoint"] == gone_endpoint:
            raise PushGoneError(gone_endpoint)
        # Live endpoint → succeed silently.

    send_alerts_push(now=_NOW, _send_push=_selective_sender)

    rows = _subscriptions_for(user_id)
    endpoints = {r.endpoint for r in rows}
    assert gone_endpoint not in endpoints, "404/410 endpoint should be pruned"
    assert live_endpoint in endpoints, "live endpoint should remain"


def test__push_job__no_op_when_no_subscriptions(api):
    name = f"push-empty-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    calls, sender = _captured_sender()
    sent = send_alerts_push(now=_NOW, _send_push=sender)
    assert sent == 0
    assert calls == []
