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
from dora_api.domain.entities.user import User
from dora_api.features.alerts.send_alerts_digest import send_alerts_digest
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

BASE = "http://localhost:5170/api"


def _set_seed_user_email(email: str | None) -> None:
    """FU-197 — `PATCH /auth/me` no longer accepts the `email` field
    (the only supported path is the verified change-email flow with
    confirmation token). Tests that need to put a specific address on
    the seed user without exercising the email-change UX flip it
    directly via the repo."""
    with app.app_context():
        repo = SqlAlchemyRepository()
        usernameField = EntityField(User, User.Fields.USERNAME)
        user = repo.get(User).one(usernameField.eq("dora"))
        assert user is not None, "expected seeded dora user"
        user.email = email
        repo.save_changes()


@pytest.fixture(autouse=True)
def _restore_user_state():
    """The shared seed user gets mutated (email, opt-in flags) by these
    tests. Other suites assert the seed user's email + a flag-off state,
    so restore both after every test in this module."""
    yield
    _set_seed_user_email("ben.talese@gmail.com")
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
    # `alerts_email_enabled`). FU-197 — go through the repo, not the
    # API, since the API no longer accepts unverified email writes.
    _set_seed_user_email(email)
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
    # FU-518 — dedup is PER ALERT KEY, not per item. A freshly-POSTed
    # expired item legitimately carries two keys (`stock:{id}:expired`
    # and, because a new item defaults to a Low stock level,
    # `stock:{id}:low_stock`), and each key earns exactly one email per
    # active cycle. The original version of this test asserted "the item
    # name never reappears", which conflated the two keys and flaked.
    # This version asserts the actual contract via the AlertInteraction
    # ledger: a stamped key is never re-stamped while its alert stays
    # active, clears when the alert clears, and re-fires fresh.
    name = f"digest-dedup-{uuid.uuid4().hex[:8]}"
    item_id = _create_expired_item(name)
    expired_key = f"stock:{item_id}:expired"
    user_id = _opt_in(email="digest-dedup@example.com")

    calls, sender = _captured_sender()
    send_alerts_digest(now=_MONDAY, _send_email=sender)
    assert len(calls) == 1
    assert expired_key in _emailed_keys_for(user_id), (
        "first digest should stamp the expired key"
    )
    first_stamps = {
        row.alert_key: row.last_emailed_at
        for row in _interactions_for(user_id)
        if row.last_emailed_at is not None
    }

    # Second pass (next day) while the alerts are still active → every
    # already-stamped key keeps its original timestamp: no key is emailed
    # twice within one active cycle. (Keys first surfaced on this pass —
    # the documented two-keys-per-item behaviour — may legitimately gain
    # a fresh stamp; they must then hold on the third pass.)
    send_alerts_digest(now=_TUESDAY, _send_email=sender)
    second_stamps = {
        row.alert_key: row.last_emailed_at
        for row in _interactions_for(user_id)
        if row.last_emailed_at is not None
    }
    for key, stamped_at in first_stamps.items():
        assert second_stamps[key] == stamped_at, (
            f"key {key} was re-emailed while its alert was still active"
        )

    # Subsequent passes — drive forward until the key set converges.
    # Seeded alerts can be date-dependent (e.g. a seeded item's
    # `stocktake_overdue` crosses into existence mid-window because seed
    # anchors derive from real wall-clock while our `now` is pinned to
    # fixed June dates — observed live 2026-07-11), and each *new* key
    # legitimately earns exactly one email. The invariant under test is
    # only that already-stamped keys never re-email while active.
    day = 1
    stamps = second_stamps
    for _ in range(6):
        pre = len(calls)
        send_alerts_digest(now=_TUESDAY + timedelta(days=day), _send_email=sender)
        day += 1
        next_stamps = {
            row.alert_key: row.last_emailed_at
            for row in _interactions_for(user_id)
            if row.last_emailed_at is not None
        }
        for key, stamped_at in stamps.items():
            assert next_stamps[key] == stamped_at, (
                f"key {key} was re-emailed while its alert was still active"
            )
        stamps = next_stamps
        if len(calls) == pre:
            break  # converged: a fully-stamped set sent nothing
    else:
        pytest.fail("digest never converged — emailed on 6 consecutive passes")

    # Clearing the alerts (delete the item) drops the keys from the
    # user's set → the stale-flag cleanup pass clears `last_emailed_at`.
    _delete_item(item_id)
    send_alerts_digest(now=_TUESDAY + timedelta(days=day), _send_email=sender)
    day += 1
    assert not any(
        key.startswith(f"stock:{item_id}:")
        for key in _emailed_keys_for(user_id)
    ), "cleared alerts should have their email stamps reset"

    # Re-firing the condition (new expired item, same name, new id → new
    # keys with no prior interaction) produces a fresh email.
    new_item = _create_expired_item(name)
    pre = len(calls)
    send_alerts_digest(now=_TUESDAY + timedelta(days=day), _send_email=sender)
    assert len(calls) == pre + 1, "re-fired condition should email fresh"
    assert name in calls[-1]["html_body"]
    assert f"stock:{new_item}:expired" in _emailed_keys_for(user_id)
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
    # them silently (no error). FU-197: email field is repo-only now.
    _set_seed_user_email(None)
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
