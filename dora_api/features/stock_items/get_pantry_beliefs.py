"""P8-07 — Zero-Input Pantry belief endpoint.

  GET /api/stock-items/beliefs

Returns the inferred belief (band + confidence + reason) for every stock
item, computed server-side (R-003) from the closed loop. The SPA overlays
these as additive "Dora thinks…" chips beside the manually-recorded level
on the stock overview + detail.

Gated on the per-user `inferred_pantry_enabled` opt-out (default on). When
a user has switched inference off, the endpoint short-circuits to
`{enabled: false, beliefs: {}}` so the client never renders the overlay —
belt-and-braces alongside the SPA's own gate.
"""
import logging
from dataclasses import asdict
from uuid import UUID

from flask import session

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.user import User
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.features.stock_items.pantry_belief import gather_beliefs_for_items
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_LOGGER = logging.getLogger(__name__)


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


@STOCK_ITEM_ROUTER.route("/beliefs", methods=["GET"])
def get_pantry_beliefs():
    repo = SqlAlchemyRepository()

    # Respect the per-user opt-out. A missing user (shouldn't happen behind
    # auth) is treated as "off" — no overlay rather than a surprise.
    user_id = _current_user_id()
    user: User | None = repo.get(User).by_id(user_id) if user_id else None
    if user is None or not user.inferred_pantry_enabled:
        return ok({"enabled": False, "beliefs": {}})

    items: list[StockItem] = (
        repo.get(StockItem).include(StockItem.Fields.STOCK_LEVEL).all()
    )
    beliefs = gather_beliefs_for_items(repo, items)
    _LOGGER.debug("pantry beliefs computed for %d items", len(beliefs))
    return ok({
        "enabled": True,
        "beliefs": {str(item_id): asdict(belief) for item_id, belief in beliefs.items()},
    })
