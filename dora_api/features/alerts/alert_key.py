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


@dataclass(frozen=True, slots=True)
class ParsedAlertKey:
    scope: str
    discriminator: str
    stock_item_id: UUID | None = None


def parse_alert_key(alert_key: str) -> ParsedAlertKey | None:
    """Parse a ``<scope>:<rest>`` key. Returns ``None`` if malformed.

    For the stock scope the form is ``stock:<uuid>:<discriminator>`` and the
    uuid is surfaced as ``stock_item_id``. Other scopes keep their
    discriminator (re-joined with ':') and carry no stock item.
    """
    parts = alert_key.split(":")
    if len(parts) < 2:
        return None
    scope = parts[0]
    if scope == SCOPE_STOCK:
        if len(parts) < 3:
            return None
        try:
            stock_item_id = UUID(parts[1])
        except ValueError:
            return None
        return ParsedAlertKey(
            scope=scope,
            discriminator=":".join(parts[2:]),
            stock_item_id=stock_item_id,
        )
    return ParsedAlertKey(scope=scope, discriminator=":".join(parts[1:]))
