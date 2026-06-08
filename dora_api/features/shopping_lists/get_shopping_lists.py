"""GET /api/shopping-lists — overview of every shopping list.

Each entry includes the line count and a "ticked / total" progress for quick
glanceability on the overview page. Detail (with full lines + selected
products) lives on GET /api/shopping-lists/<id>.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import List
from uuid import UUID

from sqlalchemy import func, select

from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class ShoppingListSummaryDto:
    shopping_list_id: UUID
    name: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    planned_shop_date: date | None
    line_count: int
    ticked_count: int


class GetShoppingListsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[ShoppingListSummaryDto]:
        # Two cheap queries are simpler than a join + group_by here, and the
        # list count is small (dozens at most). We aggregate line counts in
        # Python after a single grouped query.
        session = self.repository.session
        lists: List[ShoppingList] = self.repository.get(ShoppingList).all()

        counts: dict[UUID, tuple[int, int]] = {}
        # `(shopping_list_id, ticked) -> count` rolled up in one query.
        rows = session.execute(
            select(
                ShoppingListLine.shopping_list_id,
                ShoppingListLine.is_ticked,
                func.count(),
            ).group_by(ShoppingListLine.shopping_list_id, ShoppingListLine.is_ticked)
        ).all()
        for list_id, is_ticked, count in rows:
            total, ticked = counts.get(list_id, (0, 0))
            total += count
            if is_ticked:
                ticked += count
            counts[list_id] = (total, ticked)

        out: List[ShoppingListSummaryDto] = []
        for lst in lists:
            total, ticked = counts.get(lst.id, (0, 0))
            out.append(ShoppingListSummaryDto(
                shopping_list_id = lst.id,
                name = lst.name,
                status = lst.status,
                created_at = lst.created_at,
                completed_at = lst.completed_at,
                planned_shop_date = lst.planned_shop_date,
                line_count = total,
                ticked_count = ticked,
            ))
        # Active (most recent first), then archived (most recent first). With
        # "primary" inferred client-side, there's no stored flag to sort by.
        out.sort(
            key=lambda s: (
                s.status == SHOPPING_LIST_STATUS_DONE,
                -(s.created_at.timestamp() if s.created_at else 0),
            )
        )
        return out


@SHOPPING_LIST_ROUTER.route("", methods=["GET"])
def get_shopping_lists():
    _Logger = logging.getLogger(__name__)
    _Summaries = get_container().inject(GetShoppingListsHandler).handle()
    _Logger.debug("Returned %d shopping list summaries", len(_Summaries))
    return ok(_Summaries)
