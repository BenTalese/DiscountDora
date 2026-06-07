"""POST /api/shopping-lists/<id>/unfinish — inverse of /finish (Reopen).

The Undo system (F5) calls this to reverse a freshly-finished shopping list.
Reopen reads the server-owned `finish_snapshot` written by /finish — what the
finish changed (the list's prior is_primary, any list auto-promoted to primary,
and each restocked item's prior stock level) — so the reversal never trusts a
client-supplied snapshot (R-003: derived domain facts live on the server).

It un-finishes the list (status -> draft), clears `completed_at`, restores the
prior primary flag, demotes any sibling auto-promoted by the finish, restores
each item's prior stock level, and clears `finish_snapshot`. A list with no
snapshot (never finished, or already reopened) is a no-op beyond the status
flip.
"""
import json
import logging
from dataclasses import dataclass
from uuid import UUID

from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DRAFT,
                                                    ShoppingList)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(slots=True)
class UnfinishResponse:
    not_found: bool = False
    levels_restored: int = 0


class UnfinishShoppingListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> UnfinishResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return UnfinishResponse(not_found=True)

        # Un-finish + clear completion marker. Reopening returns to draft (the
        # user undid the finish; they didn't resume an active shop).
        lst.status = SHOPPING_LIST_STATUS_DRAFT
        lst.completed_at = None

        snapshot = {}
        if lst.finish_snapshot:
            try:
                snapshot = json.loads(lst.finish_snapshot)
            except (ValueError, TypeError):
                snapshot = {}

        if snapshot.get("was_primary"):
            lst.is_primary = True

        # If a sibling was auto-promoted to primary during finish, demote it
        # now to avoid the two-primaries footgun.
        promoted_id = snapshot.get("promoted_primary_list_id")
        if promoted_id:
            other = self.repository.get(ShoppingList).by_id(UUID(promoted_id))
            if other is not None:
                other.is_primary = False

        # Restore prior stock levels: bulk-load each StockItem + StockLevel so
        # we don't N+1 across the restored rows.
        levels_restored = 0
        restores = snapshot.get("level_restores") or []
        if restores:
            item_ids = list({UUID(r["stock_item_id"]) for r in restores})
            level_ids = list({UUID(r["stock_level_id"]) for r in restores})
            items_by_id = {
                i.id: i for i in self.repository.get(StockItem).all(
                    EntityField(StockItem, "id").in_(item_ids)
                )
            }
            levels_by_id = {
                l.id: l for l in self.repository.get(StockLevel).all(
                    EntityField(StockLevel, "id").in_(level_ids)
                )
            }
            for restore in restores:
                item = items_by_id.get(UUID(restore["stock_item_id"]))
                level = levels_by_id.get(UUID(restore["stock_level_id"]))
                if item is None or level is None:
                    continue
                item.stock_level = level
                levels_restored += 1

        # Snapshot is consumed — clear it so a re-finish writes a fresh one and
        # a double-reopen is a clean no-op.
        lst.finish_snapshot = None

        self.repository.save_changes()
        return UnfinishResponse(levels_restored=levels_restored)


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/unfinish", methods=["POST"])
def unfinish_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    response = get_container().inject(UnfinishShoppingListHandler).handle(
        shopping_list_id
    )
    if response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        "Unfinished list %s (levels_restored=%d)",
        shopping_list_id, response.levels_restored,
    )
    return no_content()
