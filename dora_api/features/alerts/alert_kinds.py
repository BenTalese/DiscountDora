"""Canonical registry of alert kinds + their default tiers (C-9.2).

Single source (R-003) for *which* inventory alert kinds exist and *which tier*
each sits in by default (PROPOSAL_ALERTS §5). The tier drives the count split
(§3.4): the bell badge counts the **actionable** tier; the **FYI** tier is shown
in the list but never inflates the badge. A per-user `AlertPreference` can
disable a kind or override its tier — this module owns the defaults those
overrides start from and validates incoming pref writes (R-010).

Kinds are emitted by `get_alerts.py`; the default tiers below stay aligned with
the per-kind severities assigned there (the four high/medium kinds are
actionable, the two low kinds are FYI). New kinds (`no_planned_meals`,
`shopping_day` — C-9.4) register here when they land.
"""

TIER_ACTIONABLE = "actionable"
TIER_FYI = "fyi"
KNOWN_TIERS = frozenset({TIER_ACTIONABLE, TIER_FYI})

# kind → default tier (PROPOSAL_ALERTS §5).
DEFAULT_TIER_BY_KIND: dict[str, str] = {
    "expired": TIER_ACTIONABLE,
    "essential_low": TIER_ACTIONABLE,
    "expiring_soon": TIER_ACTIONABLE,
    "out_of_stock": TIER_ACTIONABLE,
    "low_stock": TIER_FYI,
    "stocktake_overdue": TIER_FYI,
}
KNOWN_KINDS = frozenset(DEFAULT_TIER_BY_KIND)


def is_known_kind(kind: str) -> bool:
    return kind in KNOWN_KINDS


def is_valid_tier(tier: str) -> bool:
    return tier in KNOWN_TIERS


def default_tier_for(kind: str) -> str:
    """The kind's default tier (PROPOSAL_ALERTS §5). Defaults to *actionable*
    for an unregistered kind so a new kind is never silently hidden from the
    badge before it's added above."""
    return DEFAULT_TIER_BY_KIND.get(kind, TIER_ACTIONABLE)
