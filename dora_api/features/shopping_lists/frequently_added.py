"""GET /api/shopping-lists/frequently-added — top stock items by how often
they've been added to a shopping list.

Used by QuickAddSheet to surface "stuff you usually buy" before the user
starts typing. We count occurrences across every existing line (active and
archived) — items the user has added before, regardless of whether they
ticked them or finished the list, are still good suggestions.
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from sqlalchemy import func, select

from dora_api.domain.entities.shopping_list import ShoppingListLine
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository
from flask import request


@dataclass(frozen=True, slots=True)
class FrequentlyAddedDto:
    stock_item_id: UUID
    name: str
    stock_level_id: UUID | None
    add_count: int


class GetFrequentlyAddedHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, limit: int) -> List[FrequentlyAddedDto]:
        session = self.repository.session
        # One grouped query gets the counts; we only join StockItem for the
        # name + level so the response is self-contained.
        rows = session.execute(
            select(
                ShoppingListLine.stock_item_id,
                func.count().label("add_count"),
            ).group_by(ShoppingListLine.stock_item_id)
        ).all()
        if not rows:
            return []

        counts: dict[UUID, int] = {row[0]: int(row[1]) for row in rows}
        items = self.repository.get(StockItem).all()
        out: List[FrequentlyAddedDto] = []
        for item in items:
            count = counts.get(item.id, 0)
            if count <= 0:
                continue
            out.append(FrequentlyAddedDto(
                stock_item_id = item.id,
                name = item.name,
                stock_level_id = item.stock_level.id if item.stock_level else None,
                add_count = count,
            ))
        # Most-added first; alphabetical tiebreak so the order is stable.
        out.sort(key=lambda r: (-r.add_count, r.name.lower()))
        return out[:limit]


@SHOPPING_LIST_ROUTER.route("/frequently-added", methods=["GET"])
def get_frequently_added():
    _Logger = logging.getLogger(__name__)
    try:
        _Limit = int(request.args.get("limit", "12"))
    except (TypeError, ValueError):
        _Limit = 12
    _Limit = max(1, min(_Limit, 50))
    _Results = GetFrequentlyAddedHandler(SqlAlchemyRepository()).handle(_Limit)
    _Logger.debug("Frequently-added returned %d items (limit %d)", len(_Results), _Limit)
    return ok(_Results)
