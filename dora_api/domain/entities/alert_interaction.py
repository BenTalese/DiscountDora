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
    # delivery dedup for the web-push channel (PROPOSAL_ALERTS §4.2
    # decision: a timestamp column on this ledger, not a sibling
    # AlertDelivery table — dedup stays coarse). Set when the push job
    # sends an alert; cleared by the same job on the next run once the
    # alert key has dropped out of the user's actionable set, so the same
    # condition re-firing later notifies again. Its email sibling
    # `last_emailed_at` was dropped with the digest itself (Step-0 Q4).
    last_pushed_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        ALERT_KEY = "alert_key"
        CREATED_AT = "created_at"
        READ_AT = "read_at"
        SNOOZED_UNTIL = "snoozed_until"
        DISMISSED_AT = "dismissed_at"
        LAST_PUSHED_AT = "last_pushed_at"
