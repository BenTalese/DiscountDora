from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class AlertPreference(BaseEntity):
    """C-9.2 — one user's preference for a single alert *kind*.

    The evaluator computes the shared household truth (which items need
    attention); each user's preferences then filter *their* view and counts
    (`features/alerts/get_alerts.py`):

      - ``enabled=False`` → the kind contributes nothing to that user's list,
        counts, or (later) channel deliveries.
      - ``tier_override`` (``'actionable'`` | ``'fyi'`` | ``None``) → moves the
        kind between the badge-counted *actionable* tier and the shown-but-
        uncounted *FYI* tier, overriding the per-kind default
        (PROPOSAL_ALERTS §5; see `features/alerts/alert_kinds.py`).

    A row exists only once a user has changed a default; its absence means
    "default" (enabled + the kind's default tier). Per-user scoping here is
    legitimate preference state, NOT tenancy (PROPOSAL_ALERTS §9) — mirrors the
    per-user `AlertInteraction` ledger.
    """
    user_id: UUID
    kind: str
    enabled: bool = True
    tier_override: str | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        KIND = "kind"
        ENABLED = "enabled"
        TIER_OVERRIDE = "tier_override"
