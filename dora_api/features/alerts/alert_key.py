"""Stable alert keys: ``<scope>:<id>:<kind>``.

C-9.1 generalised the alert id from the old ``<stock_item_id>:<kind>`` to a
scoped form so non-stock alerts (meal / list / system, C-9.4+) can share the
same interaction ledger (`AlertInteraction`). The key must be **stable across
evaluations** so a persisted interaction keeps matching the same recurring
condition — the same discipline `DoraSuggestionSuppression.dedup_key` follows.

The discriminator is the per-item alert variant (e.g. ``expired``,
``essential_out``) — it is NOT always equal to the alert ``kind`` (an essential
item that is out of stock has discriminator ``essential_out`` but kind
``essential_low``), which is fine: actions route on the request body, and the
ledger only needs the key to be unique + stable.
"""
from dataclasses import dataclass
from uuid import UUID

SCOPE_STOCK = "stock"
SCOPE_MEAL = "meal"
SCOPE_LIST = "list"
SCOPE_SYSTEM = "system"


def stock_alert_key(stock_item_id: UUID, discriminator: str) -> str:
    return f"{SCOPE_STOCK}:{stock_item_id}:{discriminator}"


def list_alert_key(list_id: UUID, discriminator: str) -> str:
    return f"{SCOPE_LIST}:{list_id}:{discriminator}"


def meal_alert_key(discriminator: str) -> str:
    """Meal-scoped key with no owning id — the discriminator carries the
    stable window (e.g. ``no_planned_meals:2026-W25``)."""
    return f"{SCOPE_MEAL}:{discriminator}"


@dataclass(frozen=True, slots=True)
class ParsedAlertKey:
    scope: str
    discriminator: str
    stock_item_id: UUID | None = None
    list_id: UUID | None = None


def parse_alert_key(alert_key: str) -> ParsedAlertKey | None:
    """Parse a ``<scope>:<rest>`` key. Returns ``None`` if malformed.

    For the stock scope the form is ``stock:<uuid>:<discriminator>`` and the
    uuid is surfaced as ``stock_item_id``; for the list scope
    ``list:<uuid>:<discriminator>`` surfaces ``list_id``. Other scopes keep
    their discriminator (re-joined with ':') and carry no owning id.
    """
    parts = alert_key.split(":")
    if len(parts) < 2:
        return None
    scope = parts[0]
    if scope in (SCOPE_STOCK, SCOPE_LIST):
        if len(parts) < 3:
            return None
        try:
            owner_id = UUID(parts[1])
        except ValueError:
            return None
        return ParsedAlertKey(
            scope=scope,
            discriminator=":".join(parts[2:]),
            stock_item_id=owner_id if scope == SCOPE_STOCK else None,
            list_id=owner_id if scope == SCOPE_LIST else None,
        )
    return ParsedAlertKey(scope=scope, discriminator=":".join(parts[1:]))
