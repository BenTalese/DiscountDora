"""Per-user alert preferences (C-9.2):

  GET   /api/alerts/prefs   — this user's per-kind prefs (stored rows merged
                              with the §5 defaults, so the UI sees every kind)
  PATCH /api/alerts/prefs   — upsert one kind's pref
                              { kind, enabled?, tier_override? }

Preferences are per-user: how quiet or noisy alerts are is inherently personal,
even in a single-household install (PROPOSAL_ALERTS §9 — read/quiet state, NOT
tenancy). The evaluator (`get_alerts.py`) applies them — a disabled kind is
omitted from that user's set/counts/channels; a `tier_override` moves the kind
between the badge-counted actionable tier and the FYI tier. Absent row =
default (enabled + the kind's default tier, §5).
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.alert_preference import AlertPreference
from dora_api.features.alerts.alert_kinds import (KNOWN_KINDS, default_tier_for,
                                                  is_known_kind, is_valid_tier)
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok, unauthorized
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


@dataclass(frozen=True, slots=True)
class AlertPrefDto:
    kind: str
    enabled: bool
    tier_override: str | None
    default_tier: str
    effective_tier: str


@dataclass(frozen=True, slots=True)
class AlertPrefsDto:
    prefs: List[AlertPrefDto]


class UpdateAlertPrefRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    enabled: bool | None = None
    tier_override: str | None = None


class AlertPrefsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def _rows(self, user_id: UUID) -> dict[str, AlertPreference]:
        rows: List[AlertPreference] = self.repository.get(AlertPreference).all(
            EntityField(AlertPreference, AlertPreference.Fields.USER_ID).eq(user_id)
        )
        return {row.kind: row for row in rows}

    def get_prefs(self, user_id: UUID) -> AlertPrefsDto:
        stored = self._rows(user_id)
        prefs: List[AlertPrefDto] = []
        for kind in sorted(KNOWN_KINDS):
            row = stored.get(kind)
            enabled = row.enabled if row is not None else True
            override = row.tier_override if row is not None else None
            default_tier = default_tier_for(kind)
            prefs.append(AlertPrefDto(
                kind=kind,
                enabled=enabled,
                tier_override=override,
                default_tier=default_tier,
                effective_tier=override or default_tier,
            ))
        return AlertPrefsDto(prefs=prefs)

    def update_pref(self, user_id: UUID, request: UpdateAlertPrefRequest) -> None:
        existing = self.repository.get(AlertPreference).one(
            EntityField(AlertPreference, AlertPreference.Fields.USER_ID).eq(user_id)
            & EntityField(AlertPreference, AlertPreference.Fields.KIND).eq(request.kind)
        )
        if existing is None:
            existing = AlertPreference(user_id=user_id, kind=request.kind)
            self.repository.add(existing)
        set_fields = request.model_fields_set
        if "enabled" in set_fields and request.enabled is not None:
            existing.enabled = request.enabled
        if "tier_override" in set_fields:
            existing.tier_override = request.tier_override  # may be None to clear the override
        self.repository.save_changes()


@ALERT_ROUTER.route("/prefs", methods=["GET"])
def get_alert_prefs():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    return ok(AlertPrefsHandler(SqlAlchemyRepository()).get_prefs(user_id))


@ALERT_ROUTER.route("/prefs", methods=["PATCH"])
@has_request_body(UpdateAlertPrefRequest)
def update_alert_pref():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    request: UpdateAlertPrefRequest = get_request_body()
    # R-010 — validate against the known vocabulary on write, not just read.
    if not is_known_kind(request.kind):
        return bad_request(f"Unknown alert kind '{request.kind}'.")
    if (
        "tier_override" in request.model_fields_set
        and request.tier_override is not None
        and not is_valid_tier(request.tier_override)
    ):
        return bad_request(f"Invalid alert tier '{request.tier_override}'.")
    handler = AlertPrefsHandler(SqlAlchemyRepository())
    handler.update_pref(user_id, request)
    logging.getLogger(__name__).info("Alert pref updated: kind=%s by %s", request.kind, user_id)
    return ok(handler.get_prefs(user_id))
