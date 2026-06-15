from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class AlertInteraction(BaseEntity):
    """C-9.1 — one user's relationship to a single derived alert.

    Alerts are *derived* from current pantry state and never stored (see
    `features/alerts/get_alerts.py`): persisting the condition would go
    stale the instant the user restocks. What we persist instead is each
    user's per-alert *decisions* — whether they've read it, snoozed it
    (until `snoozed_until`), or dismissed it. Mirrors
    `DoraSuggestionSuppression`, plus a `user_id` + `read_at` because
    read/snooze are inherently per-user even in a single-household install
    (read-state is the legitimate kind of per-user scoping — NOT tenancy;
    "notify another user" stays out of scope, PROPOSAL_ALERTS §9).

    `alert_key` is the alert's stable id (`<scope>:<id>:<kind>`, e.g.
    `stock:<uuid>:expiring_soon` — see `features/alerts/alert_key.py`),
    stable across evaluations so a row keeps matching the same recurring
    condition. A row exists only once a user has interacted with the
    alert; its absence means "untouched".
    """
    user_id: UUID
    alert_key: str
    created_at: datetime
    read_at: datetime | None = None
    snoozed_until: datetime | None = None
    dismissed_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        ALERT_KEY = "alert_key"
        CREATED_AT = "created_at"
        READ_AT = "read_at"
        SNOOZED_UNTIL = "snoozed_until"
        DISMISSED_AT = "dismissed_at"
