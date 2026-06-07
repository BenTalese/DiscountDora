"""GET /api/shopping-lists/membership — which stock items are on which active lists.

Used by the stock overview to colour the cart button per row (already on
primary, on a non-primary list, on multiple unticked lists, etc) without
loading every list's lines client-side.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List
from uuid import UUID

from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class StockItemMembershipDto:
    stock_item_id: UUID
    # List IDs the item appears on, AND is still unticked. Ticked items
    # are excluded — they're effectively "done" from a quick-action POV.
    unticked_list_ids: List[UUID] = field(default_factory=list)
    # True if the item is unticked on the (single) primary list.
    on_primary: bool = False


@dataclass(frozen=True, slots=True)
class ActiveListInfoDto:
    """Lightweight summary of an active list — surfaced alongside the
    per-item membership map so the cart-button remove flow can show
    human-readable list names without an extra round-trip."""
    shopping_list_id: UUID
    name: str
    is_primary: bool


@dataclass(frozen=True, slots=True)
class MembershipDto:
    primary_shopping_list_id: UUID | None
    items: List[StockItemMembershipDto] = field(default_factory=list)
    active_lists: List[ActiveListInfoDto] = field(default_factory=list)


class GetMembershipHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> MembershipDto:
        # Active (non-archived) lists only — archived lists shouldn't paint
        # the cart button.
        active_lists: List[ShoppingList] = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
        )
        primary_id: UUID | None = next(
            (l.id for l in active_lists if l.is_primary), None
        )
        active_ids = {l.id for l in active_lists}

        # All unticked lines. We bucket in Python.
        unticked_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(False)
        )

        per_item: Dict[UUID, List[UUID]] = {}
        for line in unticked_lines:
            if line.shopping_list_id not in active_ids:
                continue
            per_item.setdefault(line.stock_item_id, []).append(line.shopping_list_id)

        items = [
            StockItemMembershipDto(
                stock_item_id = stock_item_id,
                unticked_list_ids = list_ids,
                on_primary = (primary_id is not None and primary_id in list_ids),
            )
            for stock_item_id, list_ids in per_item.items()
        ]
        active_list_infos = [
            ActiveListInfoDto(
                shopping_list_id = l.id,
                name = l.name,
                is_primary = bool(l.is_primary),
            )
            for l in active_lists
        ]
        return MembershipDto(
            primary_shopping_list_id=primary_id,
            items=items,
            active_lists=active_list_infos,
        )


@SHOPPING_LIST_ROUTER.route("/membership", methods=["GET"])
def get_membership():
    _Logger = logging.getLogger(__name__)
    _Result = get_container().inject(GetMembershipHandler).handle()
    _Logger.debug(
        "Membership: primary=%s, %d items on at least one active list",
        _Result.primary_shopping_list_id, len(_Result.items),
    )
    return ok(_Result)
