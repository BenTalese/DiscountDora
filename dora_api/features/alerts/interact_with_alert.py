"""Per-user alert interaction endpoints (C-9.1):

  POST   /api/alerts/<alert_id>/read        — mark read
  POST   /api/alerts/<alert_id>/unread      — mark unread
  POST   /api/alerts/<alert_id>/snooze      — body { days }  (default 7)
  POST   /api/alerts/<alert_id>/dismiss     — hide until the condition re-fires
  DELETE /api/alerts/<alert_id>/suppression — undo snooze/dismiss
  POST   /api/alerts/read-all               — mark every active alert read

Alerts are derived from live state, so we don't store them — we store the
user's *decisions* about them in `AlertInteraction`, keyed by the alert's
stable `<scope>:<id>:<kind>` key. The GET /alerts handler overlays these so
the badge, list, and (later) channels all agree (PROPOSAL_ALERTS §3.4).

`<alert_id>` is the scoped key; it contains ':' but no '/', so Flask's
default string converter matches it as a single path segment.
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.features.alerts.get_alerts import GetAlertsHandler
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import no_content, unauthorized
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


class SnoozeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: int = Field(default=7, ge=1, le=365)


class AlertInteractionHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def _find(self, user_id: UUID, alert_key: str) -> AlertInteraction | None:
        return self.repository.get(AlertInteraction).one(
            EntityField(AlertInteraction, AlertInteraction.Fields.USER_ID).eq(user_id)
            & EntityField(AlertInteraction, AlertInteraction.Fields.ALERT_KEY).eq(alert_key)
        )

    def _get_or_create(self, user_id: UUID, alert_key: str) -> AlertInteraction:
        existing = self._find(user_id, alert_key)
        if existing is not None:
            return existing
        interaction = AlertInteraction(
            user_id=user_id,
            alert_key=alert_key,
            created_at=datetime.now(timezone.utc),
        )
        self.repository.add(interaction)
        return interaction

    def set_read(self, user_id: UUID, alert_key: str, read: bool) -> None:
        interaction = self._get_or_create(user_id, alert_key)
        interaction.read_at = datetime.now(timezone.utc) if read else None
        self.repository.save_changes()

    def snooze(self, user_id: UUID, alert_key: str, days: int) -> None:
        interaction = self._get_or_create(user_id, alert_key)
        interaction.snoozed_until = datetime.now(timezone.utc) + timedelta(days=days)
        interaction.dismissed_at = None
        self.repository.save_changes()

    def dismiss(self, user_id: UUID, alert_key: str) -> None:
        interaction = self._get_or_create(user_id, alert_key)
        interaction.dismissed_at = datetime.now(timezone.utc)
        self.repository.save_changes()

    def clear_suppression(self, user_id: UUID, alert_key: str) -> None:
        interaction = self._find(user_id, alert_key)
        if interaction is not None:
            interaction.snoozed_until = None
            interaction.dismissed_at = None
            self.repository.save_changes()

    def mark_all_read(self, user_id: UUID) -> None:
        # Server-derived: read the user's current active set and stamp each.
        alerts = GetAlertsHandler(SqlAlchemyRepository()).handle(user_id)
        changed = False
        for alert in alerts.items:
            interaction = self._get_or_create(user_id, alert.alert_id)
            if interaction.read_at is None:
                interaction.read_at = datetime.now(timezone.utc)
                changed = True
        if changed:
            self.repository.save_changes()


@ALERT_ROUTER.route("/read-all", methods=["POST"])
def read_all_alerts():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    AlertInteractionHandler(SqlAlchemyRepository()).mark_all_read(user_id)
    return no_content()


@ALERT_ROUTER.route("/<alert_id>/read", methods=["POST"])
def mark_alert_read(alert_id: str):
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    AlertInteractionHandler(SqlAlchemyRepository()).set_read(user_id, alert_id, True)
    return no_content()


@ALERT_ROUTER.route("/<alert_id>/unread", methods=["POST"])
def mark_alert_unread(alert_id: str):
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    AlertInteractionHandler(SqlAlchemyRepository()).set_read(user_id, alert_id, False)
    return no_content()


@ALERT_ROUTER.route("/<alert_id>/snooze", methods=["POST"])
@has_request_body(SnoozeRequest)
def snooze_alert(alert_id: str):
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    _Request: SnoozeRequest = get_request_body()
    AlertInteractionHandler(SqlAlchemyRepository()).snooze(user_id, alert_id, _Request.days)
    logging.getLogger(__name__).info("Alert %s snoozed %dd by %s", alert_id, _Request.days, user_id)
    return no_content()


@ALERT_ROUTER.route("/<alert_id>/dismiss", methods=["POST"])
def dismiss_alert(alert_id: str):
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    AlertInteractionHandler(SqlAlchemyRepository()).dismiss(user_id, alert_id)
    return no_content()


@ALERT_ROUTER.route("/<alert_id>/suppression", methods=["DELETE"])
def clear_alert_suppression(alert_id: str):
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    AlertInteractionHandler(SqlAlchemyRepository()).clear_suppression(user_id, alert_id)
    return no_content()
