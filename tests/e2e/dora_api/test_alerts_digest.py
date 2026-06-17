"""C-9.7 — alerts email digest job.

Drives `send_alerts_digest` directly (the scheduler is intentionally
disabled under `is_test_env=True`, so the job has to be exercised via a
function call rather than a tick). Email sending is captured via the
`_send_email` test seam — no real SMTP, and the production code path is
unchanged (the seam defaults to `email_sender.send_email`).
"""
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import requests

from dora_api.app import app
from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.features.alerts.send_alerts_digest import send_alerts_digest
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

BASE = "http://localhost:5170/api"


@pytest.fixture(autouse=True)
def _restore_user_state():
    """The shared seed user gets mutated (email, opt-in flags) by these
    tests. Other suites assert the seed user's email + a flag-off state,
    so restore both after every test in this module."""
    yield
    requests.patch(f"{BASE}/auth/me", json={"email": "ben.talese@gmail.com"})
    requests.patch(f"{BASE}/auth/me", json={
        "alerts_email_enabled": False,
        "alerts_email_cadence": "off",
        "alerts_email_day": 0,
    })


def _any_stock_level_id() -> str:
    levels = requests.get(f"{BASE}/stock-levels").json().get("items") or []
    assert levels, "expected seeded stock levels"
    return levels[0]["stock_level_id"]


def _create_expired_item(name: str) -> str:
    """Returns the new stock-item id."""
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


def _opt_in(*, email: str, cadence: str = "daily", day: int = 0) -> UUID:
    # The seed user has no email by default; setting it here is part of the
    # opt-in (the digest skips users without an email regardless of
    # `alerts_email_enabled`).
    me = requests.patch(f"{BASE}/auth/me", json={"email": email})
    assert me.status_code == 200, me.text
    me = requests.patch(f"{BASE}/auth/me", json={
        "alerts_email_enabled": True,
        "alerts_email_cadence": cadence,
        "alerts_email_day": day,
    })
    assert me.status_code == 200, me.text
    return UUID(me.json()["user_id"])


def _opt_out() -> None:
    resp = requests.patch(f"{BASE}/auth/me", json={
        "alerts_email_enabled": False,
        "alerts_email_cadence": "off",
    })
    assert resp.status_code == 200, resp.text


def _captured_sender():
    """Returns `(calls, fn)`. `fn` matches `send_email`'s keyword shape."""
    calls: list[dict] = []
    def _capture(**kwargs):
        calls.append(kwargs)
    return calls, _capture


def _interactions_for(user_id: UUID) -> list[AlertInteraction]:
    with app.app_context():
        repo = SqlAlchemyRepository()
        return repo.get(AlertInteraction).all(
            EntityField(AlertInteraction, AlertInteraction.Fields.USER_ID).eq(user_id)
        )


def _emailed_keys_for(user_id: UUID) -> set[str]:
    return {
        row.alert_key
        for row in _interactions_for(user_id)
        if row.last_emailed_at is not None
    }


# Reasonable Monday/Tuesday anchors so weekly-cadence tests don't depend
# on real wall-clock. The job reads `now.weekday()` only — date doesn't
# otherwise matter.
_MONDAY = datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)  # weekday 0
_TUESDAY = _MONDAY + timedelta(days=1)


def test__digest__sends_to_opted_in_user_with_actionable_alert(api):
    name = f"digest-send-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    user_id = _opt_in(email="digest-send@example.com")

    calls, sender = _captured_sender()
    sent = send_alerts_digest(now=_MONDAY, _send_email=sender)

    assert sent == 1, "exactly one digest expected"
    assert len(calls) == 1, calls
    call = calls[0]
    assert call["to"] == "digest-send@example.com"
    assert "Dashy Dora" in call["subject"]
    assert name in call["html_body"]
    assert name in call["text_body"]

    emailed = _emailed_keys_for(user_id)
    matching = [k for k in emailed if name not in k or True]  # any key stamped is OK
    assert emailed, "AlertInteraction should be stamped with last_emailed_at"
    assert any(k.endswith(":expired") for k in emailed)


def test__digest__dedups_until_alert_clears_and_refires(api):
    name = f"digest-dedup-{uuid.uuid4().hex[:8]}"
    item_id = _create_expired_item(name)
    user_id = _opt_in(email="digest-dedup@example.com")

    calls, sender = _captured_sender()
    send_alerts_digest(now=_MONDAY, _send_email=sender)
    first_calls = len(calls)
    assert first_calls >= 1

    # Second pass while the alert is still active → no resend for the
    # same key (the body of any new send won't include this item).
    send_alerts_digest(now=_MONDAY, _send_email=sender)
    second_calls = len(calls)
    # Either no new email, or a new email that no longer mentions this name.
    if second_calls > first_calls:
        for c in calls[first_calls:]:
            assert name not in c["html_body"], (
                "deduped alert should not re-appear in subsequent digests"
            )

    # Clearing the alert (delete the item) drops it from the actionable
    # set → the stale-flag cleanup pass clears `last_emailed_at` for that
    # key. Re-firing the condition (new expired item with the same name)
    # produces a fresh key (different stock-item id) so the new key has
    # no prior interaction → fresh email.
    _delete_item(item_id)
    send_alerts_digest(now=_MONDAY, _send_email=sender)  # no actionable items now

    new_item = _create_expired_item(name)
    pre = len(calls)
    send_alerts_digest(now=_MONDAY, _send_email=sender)
    assert len(calls) == pre + 1, "re-fired condition should email fresh"
    assert name in calls[-1]["html_body"]
    _delete_item(new_item)


def test__digest__skips_when_cadence_is_off(api):
    name = f"digest-off-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    _opt_out()

    calls, sender = _captured_sender()
    sent = send_alerts_digest(now=_MONDAY, _send_email=sender)

    assert sent == 0
    assert not any(name in c.get("html_body", "") for c in calls)


def test__digest__weekly_cadence_only_fires_on_picked_day(api):
    name = f"digest-weekly-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    # Pick Monday (0). Wednesday (2) shouldn't trigger.
    _opt_in(email="digest-weekly@example.com", cadence="weekly", day=0)

    calls, sender = _captured_sender()

    # Wednesday → weekday 2, not the picked day → no email for this user.
    wednesday = _MONDAY + timedelta(days=2)
    send_alerts_digest(now=wednesday, _send_email=sender)
    assert not any(name in c.get("html_body", "") for c in calls)

    # Monday → weekday 0, the picked day → email fires.
    send_alerts_digest(now=_MONDAY, _send_email=sender)
    assert any(name in c.get("html_body", "") for c in calls)


def test__digest__skips_user_without_email(api):
    name = f"digest-noemail-{uuid.uuid4().hex[:8]}"
    _create_expired_item(name)
    # Opt the user in but clear their email — the candidate filter drops
    # them silently (no error).
    me = requests.patch(f"{BASE}/auth/me", json={"email": None})
    assert me.status_code == 200, me.text
    me = requests.patch(f"{BASE}/auth/me", json={
        "alerts_email_enabled": True,
        "alerts_email_cadence": "daily",
    })
    assert me.status_code == 200, me.text

    calls, sender = _captured_sender()
    sent = send_alerts_digest(now=_MONDAY, _send_email=sender)

    assert sent == 0
    assert calls == []


def test__update_me__rejects_invalid_alerts_email_cadence(api):
    resp = requests.patch(
        f"{BASE}/auth/me",
        json={"alerts_email_cadence": "hourly"},
    )
    # The handler returns a business_rule_violation for closed-set sentinels.
    assert resp.status_code in (400, 422), resp.text
    assert "alerts email cadence" in resp.text.lower()
