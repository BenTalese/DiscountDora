"""GET /api/alerts/history — the user's recent alert decisions (C-9.3).

Alerts are derived (never stored), so "history" is the audit trail of what the
user *did* about them — read / snoozed / dismissed — read from the
`AlertInteraction` ledger (C-9.1). Each row is enriched with a human label: for a
stock-scoped alert that's the item's current name (or "(removed item)" if it has
since been deleted). Answers "what was alerting me?" on the hub's History section.
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from flask import request, session

from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.alerts.alert_key import SCOPE_STOCK, parse_alert_key
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import ok, unauthorized
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


STATE_DISMISSED = "dismissed"
STATE_SNOOZED = "snoozed"
STATE_READ = "read"

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, slots=True)
class AlertHistoryEntryDto:
    alert_key: str
    kind: str                # discriminator parsed from the key (best-effort)
    label: str               # human label (stock item name if resolvable)
    state: str               # 'dismissed' | 'snoozed' | 'read'
    at: str                  # ISO timestamp of that decision
    stock_item_id: str | None
    snoozed_until: str | None


@dataclass(frozen=True, slots=True)
class AlertHistoryDto:
    entries: List[AlertHistoryEntryDto]


def _state_and_at(row: AlertInteraction):
    """The most significant decision on a ledger row + its ISO timestamp, or
    None if the row carries no decision (e.g. a cleared suppression). Dismiss
    outranks snooze outranks read — the strongest "I dealt with this" wins."""
    if row.dismissed_at is not None:
        return STATE_DISMISSED, row.dismissed_at.isoformat()
    if row.snoozed_until is not None:
        return STATE_SNOOZED, row.snoozed_until.isoformat()
    if row.read_at is not None:
        return STATE_READ, row.read_at.isoformat()
    return None


class GetAlertHistoryHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, user_id: UUID, limit: int) -> AlertHistoryDto:
        rows: List[AlertInteraction] = self.repository.get(AlertInteraction).all(
            EntityField(AlertInteraction, AlertInteraction.Fields.USER_ID).eq(user_id)
        )
        # Resolve stock-item names in one pass (bounded; history is small +
        # loaded on demand when the user expands the section).
        names: dict[UUID, str] = {
            item.id: item.name for item in self.repository.get(StockItem).all()
        }

        entries: List[AlertHistoryEntryDto] = []
        for row in rows:
            decision = _state_and_at(row)
            if decision is None:
                continue
            state, at = decision
            parsed = parse_alert_key(row.alert_key)
            kind = parsed.discriminator if parsed is not None else row.alert_key
            stock_item_id = parsed.stock_item_id if parsed is not None else None
            if parsed is not None and parsed.scope == SCOPE_STOCK and stock_item_id is not None:
                label = names.get(stock_item_id, "(removed item)")
            else:
                label = kind.replace("_", " ")
            entries.append(AlertHistoryEntryDto(
                alert_key=row.alert_key,
                kind=kind,
                label=label,
                state=state,
                at=at,
                stock_item_id=str(stock_item_id) if stock_item_id is not None else None,
                snoozed_until=row.snoozed_until.isoformat() if row.snoozed_until is not None else None,
            ))

        # Most-recent decision first. ISO timestamps from one DB share a format,
        # so a lexicographic sort is chronological (and dodges naive/aware
        # datetime comparison errors).
        entries.sort(key=lambda e: e.at, reverse=True)
        return AlertHistoryDto(entries=entries[:limit])


@ALERT_ROUTER.route("/history", methods=["GET"])
def get_alert_history():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    try:
        limit = int(request.args.get("limit", _DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = _DEFAULT_LIMIT
    limit = max(1, min(limit, _MAX_LIMIT))
    _History = GetAlertHistoryHandler(SqlAlchemyRepository()).handle(user_id, limit)
    logging.getLogger(__name__).debug(
        "Alert history: %d entries for %s", len(_History.entries), user_id
    )
    return ok(_History)
