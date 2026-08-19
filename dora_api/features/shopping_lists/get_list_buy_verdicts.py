"""Bulk buy-verdicts for one shopping list's lines.

  GET /api/shopping-lists/<id>/buy-verdicts

B6 (`IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`) — `BuyVerdictBadgeInline`
fetches `/api/stock-items/<id>/buy-verdict` per rendered line, so opening a
40-line list fires 40 requests, each re-walking the same shopping-list and
waste tables for a single item. `useBuyVerdict`'s module cache dedupes by
stock-item id; it does nothing about fan-out across *distinct* items.

This endpoint answers for the whole list in one round-trip, with a fixed
number of queries (see `gather_verdict_inputs_for_items`). The list is the
unit rather than a caller-supplied id array because the client already has a
list id, and resolving the lines server-side keeps "which items are on this
list" in one place (R-003).

Deliberately *not* gated server-side: `buy_verdict_enabled` is the SPA's
display opt-out and is about to move from a household AppSetting to a
per-user field (D-12), so gating here now would need rewriting immediately.
Parity with the per-item endpoint, which doesn't gate either.
"""
import logging
from dataclasses import asdict
from uuid import UUID

from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.stock_items.get_buy_verdict import (
    compose_verdict, gather_verdict_inputs_for_items,
)
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_LOGGER = logging.getLogger(__name__)


@SHOPPING_LIST_ROUTER.route("/<uuid:shopping_list_id>/buy-verdicts", methods=["GET"])
def get_list_buy_verdicts(shopping_list_id: UUID):
    repo = SqlAlchemyRepository()

    shopping_list: ShoppingList | None = repo.get(ShoppingList).by_id(shopping_list_id)
    if shopping_list is None:
        return not_found("ShoppingList", shopping_list_id)

    lines: list[ShoppingListLine] = repo.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
        .eq(shopping_list_id)
    )
    # A product-only line (no stock item behind it) has nothing to reason
    # about here — no recorded level, no per-item purchase history, no waste
    # events. It is skipped rather than answered with a hollow `unsure`.
    stock_item_ids = list({l.stock_item_id for l in lines if l.stock_item_id})
    if not stock_item_ids:
        return ok({"verdicts": {}})

    items: list[StockItem] = (
        repo.get(StockItem)
        .include(StockItem.Fields.STOCK_LEVEL)
        .all(EntityField(StockItem, "id").in_(stock_item_ids))
    )
    inputs_by_item = gather_verdict_inputs_for_items(repo, items)
    verdicts = {
        str(item_id): asdict(compose_verdict(inputs))
        for item_id, inputs in inputs_by_item.items()
    }
    _LOGGER.debug(
        "bulk buy-verdicts for list %s → %d verdicts over %d lines",
        shopping_list_id, len(verdicts), len(lines),
    )
    return ok({"verdicts": verdicts})
