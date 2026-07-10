"""C-9.7 — Alerts email digest job.

Scheduled daily (see ``startup.py``); per user, decides whether to send a
digest at this run and what to put in it. Re-uses the canonical alerts
evaluator (`GetAlertsHandler`) so the email body matches the in-app hub
exactly (R-003 — one source for "what counts as actionable").

Delivery dedup is coarse and stored as `AlertInteraction.last_emailed_at`
(PROPOSAL_ALERTS §4.2): once an alert key is emailed, the same key is
**not** re-emailed until it has dropped out of the user's set (so the
condition has cleared) and re-fired. The cleanup pass at the top of
each user's iteration is what resets the flag when a key disappears.

Dry-run safe: when SMTP isn't configured, `email_sender.send_email`
logs instead of sending — the job still updates the ledger so the same
alert doesn't queue up an unbounded backlog of "would-have-emailed".
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Iterable
from uuid import UUID

from dora_api.app import app
from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.domain.entities.user import (ALERTS_EMAIL_CADENCE_DAILY,
                                           ALERTS_EMAIL_CADENCE_OFF,
                                           ALERTS_EMAIL_CADENCE_WEEKLY, User)
from dora_api.features.alerts.alert_kinds import TIER_ACTIONABLE
from dora_api.features.alerts.get_alerts import (AlertDto, AlertsDto,
                                                 GetAlertsHandler)
from dora_api.infrastructure.auth_helpers import public_base_url
from dora_api.infrastructure.email_sender import render_template, send_email
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def send_alerts_digest(
    now: datetime | None = None,
    _send_email: Callable = send_email,
) -> int:
    """Process one scheduler tick. Returns the number of digests sent.

    `_send_email` is exposed for tests; production callers should leave it
    at the default. `now` defaults to the current UTC time and is also a
    test seam (lets weekday gating be exercised without freezing time).
    """
    log = logging.getLogger(__name__)
    now = now or datetime.now(timezone.utc)
    sent = 0
    try:
        with app.app_context():
            repository = SqlAlchemyRepository()
            candidates = _opted_in_users(repository)
            for user in candidates:
                try:
                    if _process_user(repository, user, now, _send_email):
                        sent += 1
                except Exception as exc:  # noqa: BLE001
                    # One bad user must never sink the whole batch — log
                    # and move on. The same alert will reappear on the
                    # next tick.
                    log.warning(
                        "alerts_digest: user %s failed: %s", user.id, exc,
                    )
            if sent:
                log.info("alerts_digest: sent %d digest(s) at %s",
                         sent, now.isoformat())
    except Exception as exc:  # noqa: BLE001
        # Top-level guard mirrors `prune_audit_events`: the job is best-
        # effort, never a poison pill for the API.
        log.warning("alerts_digest: job failed: %s", exc)
    return sent


def _opted_in_users(repository: SqlAlchemyRepository) -> list[User]:
    enabled = EntityField(User, User.Fields.ALERTS_EMAIL_ENABLED).eq(True)
    users: list[User] = repository.get(User).all(enabled)
    # Email + cadence filter in Python rather than as another field
    # condition — the candidate set is small (per-household installs),
    # and the checks are cheap and read clearly here.
    return [
        u for u in users
        if u.email and u.alerts_email_cadence != ALERTS_EMAIL_CADENCE_OFF
    ]


def _process_user(
    repository: SqlAlchemyRepository,
    user: User,
    now: datetime,
    sender: Callable,
) -> bool:
    """Send this user's digest if one is due. Returns True if sent."""
    if not _is_send_day(user, now):
        return False

    alerts: AlertsDto = GetAlertsHandler(SqlAlchemyRepository()).handle(
        user_id=user.id, now=now,
    )
    current_keys = _all_known_keys(alerts)

    # Stale-flag cleanup: any prior email-stamp for an alert key the user
    # no longer has resets, so a future re-fire of the same condition
    # produces a fresh send.
    interactions_by_key = _interactions_by_key(repository, user.id)
    dirty = False
    for key, row in interactions_by_key.items():
        if row.last_emailed_at is not None and key not in current_keys:
            row.last_emailed_at = None
            dirty = True

    # Build the send-set: active alerts (snoozed/dismissed already
    # filtered by GetAlertsHandler) the user hasn't already been emailed
    # about this cycle.
    to_email: list[AlertDto] = [
        a for a in alerts.items
        if interactions_by_key.get(a.alert_id, _NO_ROW).last_emailed_at is None
    ]
    if not to_email:
        if dirty:
            repository.save_changes()
        return False

    actionable = [a for a in to_email if a.tier == TIER_ACTIONABLE]
    fyi = [a for a in to_email if a.tier != TIER_ACTIONABLE]
    cadence_label = (
        "daily" if user.alerts_email_cadence == ALERTS_EMAIL_CADENCE_DAILY
        else "weekly"
    )
    subject = (
        f"Dashy Dora — {len(actionable)} alert"
        f"{'' if len(actionable) == 1 else 's'} need your attention"
        if actionable
        else f"Dashy Dora — {cadence_label} alerts digest"
    )
    html_body = render_template(
        "alerts_digest.html",
        subject=subject,
        username=user.username,
        cadence=cadence_label,
        actionable=actionable,
        fyi=fyi,
        alerts_url=f"{public_base_url()}/alerts",
    )
    text_body = _render_text_digest(user.username, cadence_label, actionable, fyi)

    sender(
        to=user.email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )

    # Stamp the ledger for everything we just emailed. Upsert: existing
    # row gets the timestamp, missing row gets created with it.
    for alert in to_email:
        row = interactions_by_key.get(alert.alert_id)
        if row is None:
            row = AlertInteraction(
                user_id=user.id,
                alert_key=alert.alert_id,
                created_at=now,
                last_emailed_at=now,
            )
            repository.add(row)
            interactions_by_key[alert.alert_id] = row
        else:
            row.last_emailed_at = now

    repository.save_changes()
    return True


def _is_send_day(user: User, now: datetime) -> bool:
    """Daily cadence always sends; weekly only on the user's picked day."""
    if user.alerts_email_cadence == ALERTS_EMAIL_CADENCE_DAILY:
        return True
    if user.alerts_email_cadence == ALERTS_EMAIL_CADENCE_WEEKLY:
        return now.weekday() == int(user.alerts_email_day)
    return False


def _all_known_keys(alerts: AlertsDto) -> set[str]:
    """All keys the user currently has a relationship with — active +
    snoozed. A key that's nowhere in this set is "gone for now" and the
    email-flag for it should be cleared."""
    keys: set[str] = {a.alert_id for a in alerts.items}
    keys.update(a.alert_id for a in alerts.snoozed)
    return keys


def _interactions_by_key(
    repository: SqlAlchemyRepository,
    user_id: UUID,
) -> dict[str, AlertInteraction]:
    rows: list[AlertInteraction] = repository.get(AlertInteraction).all(
        EntityField(AlertInteraction, AlertInteraction.Fields.USER_ID).eq(user_id)
    )
    return {row.alert_key: row for row in rows}


def _render_text_digest(
    username: str,
    cadence: str,
    actionable: Iterable[AlertDto],
    fyi: Iterable[AlertDto],
) -> str:
    """Plain-text companion for clients that won't render HTML."""
    lines = [f"Hi {username},", "", f"Your {cadence} alerts digest:", ""]
    a_list = list(actionable)
    if a_list:
        lines.append(f"NEEDS ACTION ({len(a_list)}):")
        for alert in a_list:
            lines.append(f"  - {alert.message}")
            if alert.detail:
                lines.append(f"      {alert.detail}")
        lines.append("")
    f_list = list(fyi)
    if f_list:
        lines.append(f"HEADS-UP ({len(f_list)}):")
        for alert in f_list:
            lines.append(f"  - {alert.message}")
            if alert.detail:
                lines.append(f"      {alert.detail}")
        lines.append("")
    lines.append(f"Open alerts: {public_base_url()}/alerts")
    lines.append("")
    lines.append("Manage your channels in Settings → Preferences.")
    return "\n".join(lines)


# Sentinel used so `interactions_by_key.get(key, _NO_ROW).last_emailed_at`
# reads cleanly without an explicit `is None` check at every callsite.
_NO_ROW = AlertInteraction(
    user_id=UUID(int=0),
    alert_key="",
    created_at=datetime.fromtimestamp(0, tz=timezone.utc),
)
