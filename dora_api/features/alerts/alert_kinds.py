"""Canonical registry of alert kinds + their severities (C-9.2).

Single source (R-003) for *which* alert kinds exist and *how loud* each is.
Severity is the only importance scale — the actionable/FYI split is **derived**
from it (`is_actionable`), never stored and never per-user overridable. That is
the Step-0 answer to Q3 in `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`: severity,
tier and a per-user `tier_override` were three encodings of one idea, kept in
step by convention, and the row/bell disagreements (B2, B3) grew in the gaps.

The badge counts the actionable set; FYI kinds are listed but never inflate it.
A per-user `AlertPreference` can still disable a kind outright — "as quiet or
noisy as they want" (feedback L441) — it just can't reclassify one.

**Eight kinds, deliberately.** Step-0 Q1 cut `out_of_stock`, `low_stock` and
`stocktake_overdue`: owner's rule is *"we want people to actually pay attention
when there's a notification"*, and those three fired constantly on conditions
already legible elsewhere — the row's own level band, and the stocktake runner's
queue. Do not re-add a kind for a condition that is already visible where the
user is looking; that is the noise this registry exists to hold back.

Kinds are emitted by `get_alerts.py`. The three stock kinds are per-item and feed
the stock-overview attention rule; the nudges are household-level and never touch
a stock row; `price_drop` is per-user (a watch is one person's).

**Every alert is one episode of its condition** (owner 2026-10-15: *"there should
be well defined points when alerts will appear and not appear"*). Its key carries
the fact that started it (an expiry date, the day a level changed, a planned shop
date, a price observation), so it fires once, a dismissal holds for that episode,
and the next episode is a new alert. Nothing re-fires as a day count ticks down.
See `alert_key.py`.
"""

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

TIER_ACTIONABLE = "actionable"
TIER_FYI = "fyi"

# Ordinal — the UI sorts high first. One home for the order (R-003).
SEVERITY_ORDER = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}

# kind → severity.
SEVERITY_BY_KIND: dict[str, str] = {
    # ── Per-item: these three ARE the stock-overview attention rule ──
    "expired": SEVERITY_HIGH,
    "essential_low": SEVERITY_HIGH,      # essential, low or out
    "expiring_soon": SEVERITY_MEDIUM,
    # ── Household-level nudges (no stock item) ──
    "no_planned_meals": SEVERITY_LOW,
    "shopping_day": SEVERITY_LOW,
    # Owner 2026-10-15 — "Did you forget your shopping?": the planned shop day
    # has passed and the list is still open. Split off `shopping_day`, which
    # used to cover both and so shared one dismissal with it.
    "shopping_overdue": SEVERITY_MEDIUM,
    "meal_reconcile_overdue": SEVERITY_LOW,
    # A product the user watches reached their price (owner 2026-10-15; the
    # `PriceAlert` rows existed since 2026-06 but nothing ever fired them).
    "price_drop": SEVERITY_MEDIUM,
}
KNOWN_KINDS = frozenset(SEVERITY_BY_KIND)

# The kinds that can put a stock row into "needs attention". Named here rather
# than re-derived from "has a stock_item_id" at each call site, so adding a
# per-item kind is one edit (R-003).
ATTENTION_KINDS = frozenset({"expired", "essential_low", "expiring_soon"})


def is_known_kind(kind: str) -> bool:
    return kind in KNOWN_KINDS


def severity_for(kind: str) -> str:
    """The kind's severity. An unregistered kind is treated as HIGH so a new
    kind is never silently hidden from the badge before it's added above."""
    return SEVERITY_BY_KIND.get(kind, SEVERITY_HIGH)


def is_actionable(severity: str) -> bool:
    """The derived tier. High and medium need you; low is FYI."""
    return severity in (SEVERITY_HIGH, SEVERITY_MEDIUM)


def tier_for(kind: str) -> str:
    """Convenience for DTOs that still surface a tier label to the client."""
    return TIER_ACTIONABLE if is_actionable(severity_for(kind)) else TIER_FYI
