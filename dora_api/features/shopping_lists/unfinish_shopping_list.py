"""POST /api/shopping-lists/<id>/unfinish — inverse of /finish.

The Undo system (F5) calls this to reverse a freshly-finished shopping
list. The client captures a snapshot before finishing — "was this the
primary list?", "what level was each ticked item on?" — and posts it
back here.

Why client-side snapshots instead of server-side history: finish writes
through to multiple tables (the list, every ticked item's level, the
new-primary promotion) and we don't have an audit log. Capturing the
relevant fields at call-time is the cheapest way to get a reliable
inverse without a schema change.

This endpoint is intentionally narrow: it un-archives the list, clears
`completed_at`, sets `is_in_progress` back to False (the user didn't
*resume*, they undid the finish), and applies the prior-level restores.
If another list was auto-promoted to primary by the finish, the client
can ask us to demote it via `demote_primary_list_id`.
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.shopping_list import ShoppingList
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import no_content, not_found
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


class LevelRestore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    stock_level_id: UUID


class UnfinishShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    was_primary: bool = False
    # Optional: a list that was auto-promoted to primary when the source
    # list finished. Undoing the finish should demote it again, otherwise
    # the user ends up with two primaries after a quick undo.
    demote_primary_list_id: UUID | None = None
    level_restores: List[LevelRestore] = []


@dataclass(slots=True)
class UnfinishResponse:
    not_found: bool = False
    levels_restored: int = 0


class UnfinishShoppingListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self,
        shopping_list_id: UUID,
        request: UnfinishShoppingListRequest,
    ) -> UnfinishResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return UnfinishResponse(not_found=True)

        # Un-archive + clear completion marker.
        lst.is_archived = False
        lst.completed_at = None
        lst.is_in_progress = False
        # Restore primary flag — we don't blindly set True because the
        # caller might have multiple primaries already; trust the snapshot.
        if request.was_primary:
            lst.is_primary = True

        # If a sibling was auto-promoted to primary during finish, demote
        # it now to avoid the two-primaries footgun.
        if request.demote_primary_list_id is not None:
            other = self.repository.get(ShoppingList).by_id(request.demote_primary_list_id)
            if other is not None:
                other.is_primary = False

        # Level restores: look up each StockItem + StockLevel in bulk so
        # we don't N+1 across the ticked rows.
        levels_restored = 0
        if request.level_restores:
            item_ids = list({r.stock_item_id for r in request.level_restores})
            level_ids = list({r.stock_level_id for r in request.level_restores})
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
            for restore in request.level_restores:
                item = items_by_id.get(restore.stock_item_id)
                level = levels_by_id.get(restore.stock_level_id)
                if item is None or level is None:
                    continue
                item.stock_level = level
                levels_restored += 1

        self.repository.save_changes()
        return UnfinishResponse(levels_restored=levels_restored)


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/unfinish", methods=["POST"])
@has_request_body(UnfinishShoppingListRequest)
def unfinish_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    request: UnfinishShoppingListRequest = get_request_body()
    response = get_container().inject(UnfinishShoppingListHandler).handle(
        shopping_list_id, request
    )
    if response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        "Unfinished list %s (levels_restored=%d, was_primary=%s)",
        shopping_list_id, response.levels_restored, request.was_primary,
    )
    return no_content()
