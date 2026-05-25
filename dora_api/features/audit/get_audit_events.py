"""GET /api/audit/events — list with filters; admin-only.
   GET /api/audit/events/<id> — single event detail; admin-only.

Filters (all optional, AND'd):
    source        — dapi|mapi|emailer|web|system
    severity      — debug|info|warn|error|audit (comma-separated)
    actor_user_id — UUID
    action        — exact match (autocomplete-driven on the frontend)
    entity_type   — exact match
    entity_id     — UUID
    request_id    — exact (used by "Find related" in the admin UI)
    occurred_from — ISO datetime, inclusive
    occurred_to   — ISO datetime, exclusive

Pagination via `page=` (1-based) + `size=` (default 50, max 500).
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from http.client import FORBIDDEN
from typing import Any
from uuid import UUID

from flask import request, session
from sqlalchemy import and_, desc, func, select

from dora_api.app import db
from dora_api.domain.entities.audit_event import AuditEvent
from dora_api.domain.entities.user import User
from dora_api.features.routers import AUDIT_ROUTER
from dora_api.infrastructure.api_response import (
    bad_request, not_found, ok, paginated, ProblemDetails, unprocessable_entity,
)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Cap on `size` so the admin UI can't accidentally fetch the whole table.
MAX_PAGE_SIZE = 500
DEFAULT_PAGE_SIZE = 50


@dataclass(frozen=True, slots=True)
class AuditEventDto:
    audit_event_id: str
    occurred_at: str
    source: str
    severity: str
    action: str
    actor_user_id: str | None
    actor_username: str | None
    actor_ip: str | None
    entity_type: str | None
    entity_id: str | None
    request_id: str | None
    payload: Any


def _require_admin() -> Any | None:
    """Return a Forbidden response if the caller isn't an admin. Returns
    None when the request may proceed."""
    raw = session.get("user_id")
    if not raw:
        # Middleware should have rejected this already, but belt-and-braces.
        return unprocessable_entity(ProblemDetails(
            detail="Authentication required.",
            status=403, errors={}, title="Forbidden.",
            type="https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3",
        ))
    try:
        user_id = UUID(raw)
    except (ValueError, TypeError):
        return _forbidden("Invalid session.")
    user = SqlAlchemyRepository().get(User).by_id(user_id)
    if user is None or not user.is_admin:
        return _forbidden("Admin role required.")
    return None


def _forbidden(detail: str):
    from flask import jsonify
    response = jsonify(ProblemDetails(
        detail=detail,
        status=FORBIDDEN, errors={}, title="Forbidden.",
        type="https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3",
    ))
    response.content_type = 'application/problem+json'
    response.status_code = FORBIDDEN
    return response


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _build_filters() -> list:
    """Translate query-string args into SQLAlchemy where clauses."""
    table = db.metadata.tables["AuditEvent"]
    clauses = []

    def _trimmed(key: str) -> str | None:
        v = request.args.get(key)
        if v is None:
            return None
        v = v.strip()
        return v or None

    source = _trimmed("source")
    if source:
        clauses.append(table.c.source == source)

    severity = _trimmed("severity")
    if severity:
        tokens = [t.strip() for t in severity.split(",") if t.strip()]
        if tokens:
            clauses.append(table.c.severity.in_(tokens))

    actor = _trimmed("actor_user_id")
    if actor:
        try:
            clauses.append(table.c.actor_user_id == UUID(actor))
        except (ValueError, TypeError):
            pass

    action = _trimmed("action")
    if action:
        clauses.append(table.c.action == action)

    entity_type = _trimmed("entity_type")
    if entity_type:
        clauses.append(table.c.entity_type == entity_type)

    entity_id = _trimmed("entity_id")
    if entity_id:
        try:
            clauses.append(table.c.entity_id == UUID(entity_id))
        except (ValueError, TypeError):
            pass

    req_id = _trimmed("request_id")
    if req_id:
        clauses.append(table.c.request_id == req_id)

    occurred_from = _parse_iso(_trimmed("occurred_from"))
    if occurred_from is not None:
        clauses.append(table.c.occurred_at >= occurred_from)

    occurred_to = _parse_iso(_trimmed("occurred_to"))
    if occurred_to is not None:
        clauses.append(table.c.occurred_at < occurred_to)

    return clauses


def _row_to_dto(row: dict, username_by_id: dict[UUID, str]) -> AuditEventDto:
    actor_uuid: UUID | None = row.get("actor_user_id")
    payload_raw = row.get("payload")
    payload_parsed: Any = None
    if payload_raw:
        try:
            payload_parsed = json.loads(payload_raw)
        except (ValueError, TypeError):
            payload_parsed = payload_raw
    occurred = row.get("occurred_at")
    return AuditEventDto(
        audit_event_id=str(row.get("id")),
        occurred_at=occurred.isoformat() if isinstance(occurred, datetime) else str(occurred),
        source=row.get("source") or "",
        severity=row.get("severity") or "",
        action=row.get("action") or "",
        actor_user_id=str(actor_uuid) if actor_uuid else None,
        actor_username=(
            username_by_id.get(actor_uuid) if isinstance(actor_uuid, UUID) else None
        ),
        actor_ip=row.get("actor_ip"),
        entity_type=row.get("entity_type"),
        entity_id=str(row["entity_id"]) if row.get("entity_id") else None,
        request_id=row.get("request_id"),
        payload=payload_parsed,
    )


def _resolve_usernames(actor_ids: list[UUID]) -> dict[UUID, str]:
    if not actor_ids:
        return {}
    user_table = db.metadata.tables["User"]
    rows = db.session.execute(
        select(user_table.c.id, user_table.c.username).where(
            user_table.c.id.in_(actor_ids),
        ),
    ).all()
    return {r[0]: r[1] for r in rows}


@AUDIT_ROUTER.route("/events", methods=["GET"])
def get_audit_events():
    _Logger = logging.getLogger(__name__)
    forbidden = _require_admin()
    if forbidden is not None:
        return forbidden

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        return bad_request("page must be an integer.")
    try:
        size = int(request.args.get("size", str(DEFAULT_PAGE_SIZE)))
    except ValueError:
        return bad_request("size must be an integer.")
    if page < 1:
        return bad_request("page must be ≥ 1.")
    if size < 1 or size > MAX_PAGE_SIZE:
        return bad_request(
            f"size must be between 1 and {MAX_PAGE_SIZE} (default {DEFAULT_PAGE_SIZE})."
        )

    table = db.metadata.tables["AuditEvent"]
    clauses = _build_filters()
    where_clause = and_(*clauses) if clauses else None

    total_query = select(func.count()).select_from(table)
    if where_clause is not None:
        total_query = total_query.where(where_clause)
    total = db.session.execute(total_query).scalar() or 0

    rows_query = select(table).order_by(desc(table.c.occurred_at)).limit(size).offset(
        (page - 1) * size
    )
    if where_clause is not None:
        rows_query = rows_query.where(where_clause)
    rows = db.session.execute(rows_query).mappings().all()

    # Resolve actor usernames in one query so the admin UI doesn't N+1.
    actor_ids = [
        r["actor_user_id"] for r in rows
        if isinstance(r.get("actor_user_id"), UUID)
    ]
    usernames = _resolve_usernames(actor_ids)

    items = [_row_to_dto(dict(r), usernames) for r in rows]
    _Logger.debug("Audit events page=%d size=%d returned %d/%d", page, size, len(items), total)
    return paginated(items, total, page, size)


@AUDIT_ROUTER.route("/events/<event_id>", methods=["GET"])
def get_audit_event(event_id: str):
    forbidden = _require_admin()
    if forbidden is not None:
        return forbidden
    try:
        parsed_id = UUID(event_id)
    except (ValueError, TypeError):
        return bad_request("event_id must be a UUID.")
    table = db.metadata.tables["AuditEvent"]
    row = db.session.execute(
        select(table).where(table.c.id == parsed_id),
    ).mappings().first()
    if row is None:
        return not_found("AuditEvent", parsed_id)
    actor_uuid = row.get("actor_user_id")
    usernames = _resolve_usernames([actor_uuid] if isinstance(actor_uuid, UUID) else [])
    return ok(_row_to_dto(dict(row), usernames))
