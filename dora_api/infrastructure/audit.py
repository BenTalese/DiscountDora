"""Persisted audit log.

Privacy policy:
    Payloads must NEVER contain raw credentials, full request bodies, or
    PII secrets. `scrub(payload)` drops a known-bad key set before each
    write — adjust SCRUBBED_KEYS rather than scrubbing in callers. New
    sensitive fields land here.

Two entry points:
    - emit(action, *, source, severity, ...)
        Direct call from service-layer code when a route-level event
        isn't descriptive enough (e.g. `stock_item.auto_added_to_list`).
    - The dora_api middleware (`auto_audit_after_request`) emits one
        event per mutating request, deriving `action` from the endpoint
        name and `entity_id` from the response when it can be detected.

Auth endpoints additionally emit explicit success/failure events from
inside the handler because middleware can't reliably tell a wrong-
password 200-with-body from a real login from the status code alone.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from flask import has_request_context, request, session

from dora_api.app import db
from dora_api.domain.entities.audit_event import (
    ALLOWED_SEVERITIES, ALLOWED_SOURCES, AuditEvent,
    SEVERITY_AUDIT, SEVERITY_INFO, SOURCE_DAPI, SOURCE_SYSTEM,
)
from dora_api.infrastructure.log_context import get_request_id


# Keys we always drop from payloads. Case-insensitive substring match —
# "password", "x-api-key", "auth-token" etc. all get stripped.
SCRUBBED_KEYS: frozenset[str] = frozenset({
    "password", "password_hash", "passwordconfirm", "current_password",
    "new_password", "secret", "token", "api_key", "apikey",
    "authorization", "cookie", "set-cookie",
})

# Endpoints we never auto-audit (idempotent + frequent enough that a row
# per call would dominate the table).
_NO_AUDIT_ENDPOINTS: frozenset[str] = frozenset({
    "submit_client_log",   # already persisted via its own emit path
    "health_check",
    "login",               # handler emits an explicit auth.login.* row
    "logout",              # idempotent, not worth a row per call
})

# Endpoint-name → (entity_type, action_suffix) for common verb prefixes.
# Falls through to `_default_action_for` for everything else.
_VERB_MAP: dict[str, str] = {
    "create": "created",
    "register": "registered",
    "update": "updated",
    "patch": "updated",
    "delete": "deleted",
    "remove": "removed",
    "restore": "restored",
    "add": "added",
    "import": "imported",
    "export": "exported",
    "bulk": "bulk",
    "move": "moved",
    "clear": "cleared",
}


def _scrub(value: Any) -> Any:
    """Recursively strip SCRUBBED_KEYS from a dict. Lists pass through,
    primitives pass through, deep dicts get the same treatment.
    """
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if any(bad in k.lower() for bad in SCRUBBED_KEYS):
                out[k] = "***redacted***"
                continue
            out[k] = _scrub(v)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


# Public helper — keep the name explicit on the outside so it's grep-able.
def scrub(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    cleaned = _scrub(payload)
    return cleaned if isinstance(cleaned, dict) else {"value": cleaned}


def _default_action_for(endpoint_name: str) -> str:
    """Derive a verb-noun action from an endpoint function name. Handles
    snake_case create/update/delete naming idiomatically; falls back to
    the raw endpoint for everything else.
    """
    # Trim leading verb if it matches our map.
    parts = endpoint_name.split("_")
    if parts and parts[0] in _VERB_MAP:
        noun = "_".join(parts[1:]) or "resource"
        return f"{noun}.{_VERB_MAP[parts[0]]}"
    return endpoint_name


_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _entity_id_from_response(response_body: Any) -> UUID | None:
    """Best-effort entity-id extraction. Looks for an `id` or `<x>_id`
    field on a dict response, then falls back to a UUID-shaped string
    anywhere in the body.
    """
    if isinstance(response_body, dict):
        for key in ("id", "stock_item_id", "shopping_list_id", "recipe_id",
                    "meal_id", "meal_plan_id", "stock_location_id"):
            value = response_body.get(key)
            if value:
                try:
                    return UUID(str(value))
                except (ValueError, TypeError):
                    continue
    if isinstance(response_body, str):
        match = _UUID_RE.search(response_body)
        if match:
            try:
                return UUID(match.group(0))
            except (ValueError, TypeError):
                return None
    return None


def emit(
    action: str,
    *,
    source: str = SOURCE_DAPI,
    severity: str = SEVERITY_INFO,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
    actor_user_id: UUID | None = None,
    actor_ip: str | None = None,
    request_id: str | None = None,
    occurred_at: datetime | None = None,
) -> None:
    """Persist an audit row. Never raises — logging failures must not
    take down the actual feature.

    `source` and `severity` are validated against the entity enums;
    invalid values get rewritten to safe defaults rather than blocking
    the audit (we'd rather record a malformed event than nothing at
    all).
    """
    _Logger = logging.getLogger(__name__)
    try:
        if source not in ALLOWED_SOURCES:
            source = SOURCE_SYSTEM
        if severity not in ALLOWED_SEVERITIES:
            severity = SEVERITY_INFO

        # Pull request-bound context when running inside a Flask request.
        if has_request_context():
            if actor_user_id is None:
                raw = session.get("user_id")
                if raw:
                    try:
                        actor_user_id = UUID(raw)
                    except (ValueError, TypeError):
                        actor_user_id = None
            if actor_ip is None:
                actor_ip = request.remote_addr
            if request_id is None:
                request_id = get_request_id()
                if request_id == "-":
                    request_id = None

        scrubbed = scrub(payload)
        payload_json: str | None = None
        if scrubbed is not None:
            try:
                payload_json = json.dumps(scrubbed, default=str)
            except (TypeError, ValueError):
                payload_json = json.dumps({"_serialise_error": True})

        row = AuditEvent(
            id=uuid4(),
            occurred_at=occurred_at or datetime.now(timezone.utc),
            source=source,
            actor_user_id=actor_user_id,
            actor_ip=actor_ip,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            payload=payload_json,
            severity=severity,
        )
        db.session.add(row)
        db.session.commit()
    except Exception as exc:  # noqa: BLE001
        try:
            db.session.rollback()
        except Exception:  # noqa: BLE001
            pass
        _Logger.warning("audit.emit failed for action=%s: %s", action, exc)


# ── Middleware hook ────────────────────────────────────────────────────

_MUTATING_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def auto_audit_after_request(response):
    """`after_app_request` callback. One row per mutating /api/* request,
    skipping the explicit no-audit set (and obviously every GET). Errors
    here never bubble — audit must be best-effort.
    """
    try:
        if request.method.upper() not in _MUTATING_METHODS:
            return response
        if not (request.path or "").startswith("/api/"):
            return response
        endpoint = (request.endpoint or "").split(".")[-1]
        if not endpoint or endpoint in _NO_AUDIT_ENDPOINTS:
            return response

        # Don't auto-audit failures — explicit auth emits cover the
        # "login failed" case; everything else surfaces in logs already.
        if response.status_code >= 400:
            return response

        # Try to extract the affected entity id from the response body.
        # Don't choke on non-JSON or empty bodies.
        body_for_id: Any = None
        try:
            if response.is_json:
                body_for_id = response.get_json(silent=True)
        except Exception:  # noqa: BLE001
            body_for_id = None

        emit(
            action=_default_action_for(endpoint),
            severity=SEVERITY_AUDIT,
            entity_id=_entity_id_from_response(body_for_id),
            payload={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "auto_audit_after_request failed: %s", exc,
        )
    return response
