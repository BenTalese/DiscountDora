from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class AlertPreference(BaseEntity):
    """C-9.2 — one user's on/off switch for a single alert *kind*.

    The evaluator computes the shared household truth (which items need
    attention); this filters *that user's* view and counts
    (`features/alerts/get_alerts.py`): ``enabled=False`` → the kind contributes
    nothing to their list, counts, row outlines, or channel deliveries.

    That is the whole preference model. A ``tier_override`` used to live here,
    moving a kind between the badge-counted actionable tier and FYI; it was
    deleted at Step-0 Q3 (`IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`) because it
    made "is this actionable?" a per-user answer that the stock rows could not
    see — the direct cause of B2. Tier is now derived from severity. Keep this
    entity a switch; if a kind needs a different weight, change its severity in
    `alert_kinds.py` for everyone.

    A row exists only once a user has turned a kind off; its absence means
    enabled. Per-user scoping here is legitimate preference state, NOT tenancy
    (PROPOSAL_ALERTS §9) — mirrors the per-user `AlertInteraction` ledger.
    """
    user_id: UUID
    kind: str
    enabled: bool = True

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        KIND = "kind"
        ENABLED = "enabled"
