from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# String constants rather than Python enums — Alembic column types and
# the existing repository builder both prefer plain str/int comparisons.
SOURCE_DAPI = "dapi"
SOURCE_MAPI = "mapi"
SOURCE_EMAILER = "emailer"
SOURCE_WEB = "web"
SOURCE_SYSTEM = "system"
ALLOWED_SOURCES = (SOURCE_DAPI, SOURCE_MAPI, SOURCE_EMAILER, SOURCE_WEB, SOURCE_SYSTEM)

SEVERITY_DEBUG = "debug"
SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_ERROR = "error"
SEVERITY_AUDIT = "audit"
ALLOWED_SEVERITIES = (
    SEVERITY_DEBUG, SEVERITY_INFO, SEVERITY_WARN, SEVERITY_ERROR, SEVERITY_AUDIT,
)


@dataclass
class AuditEvent(BaseEntity):
    """One persisted audit row. Action is a dotted verb-noun like
    `stock_item.created` or `auth.login.failed`; payload carries minimal
    scrubbed context (no passwords, no PII secrets, see audit.scrub).
    """
    occurred_at: datetime
    source: str
    action: str
    severity: str
    actor_user_id: UUID | None = None
    actor_ip: str | None = None
    entity_type: str | None = None
    entity_id: UUID | None = None
    request_id: str | None = None
    payload: str | None = None  # JSON-encoded blob

    class Fields(BaseEntity.Fields):
        OCCURRED_AT = "occurred_at"
        SOURCE = "source"
        ACTOR_USER_ID = "actor_user_id"
        ACTOR_IP = "actor_ip"
        ACTION = "action"
        ENTITY_TYPE = "entity_type"
        ENTITY_ID = "entity_id"
        REQUEST_ID = "request_id"
        PAYLOAD = "payload"
        SEVERITY = "severity"
