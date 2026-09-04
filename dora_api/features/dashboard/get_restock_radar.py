"""GET /api/dashboard/restock-radar — what just ran out, and what just went low.

Owner feedback, 2026-09-04: *"Restock radar looks like it could be useful. I
don't know how it works under the hood, but I think showing a list of most
recently out of stock and a list of most recently low (one on left, one on
right) could be good."*

What it used to show was `/reports/keeps-running-out` — a genuinely clever
signal (how often an item was *already out* at the moment somebody added it to
a list, i.e. "you ran out before you got round to restocking it"), and the
reports review rated it the most insightful thing on either surface. But it is
a **history** signal: it ranks by a lifetime count, so the card looked
identical week after week and the "radar" never swept. It also needs months of
list history before it says anything, which is why a young install saw only the
empty state.

This is the present tense of the same idea: the things that changed band most
recently, which is what a radar is for. `keeps-running-out` is untouched and
still on the reports page, where a lifetime ranking belongs.

`stock_level_last_updated` is the clock, not a `ConsumptionEvent` scan: the
question is "when did this item become out", and that column *is* when its band
last changed. An event scan would additionally need deduping per item and
reconciling against the current level, to arrive at the same answer more
expensively.

Only items **currently** in the band are listed. "Recently went out" about
something you have since restocked is not a restock cue, it is a diary entry.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import (LOW_STOCK_SEQUENCE,
                                          OUT_OF_STOCK_SEQUENCE)
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.features.stock_items._level_access import resolve_levels_by_item
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

# Per column. Five rows twice is already the tallest card on the dashboard;
# the "Stock →" link carries anyone who wants the full picture.
MAX_PER_COLUMN = 5


@dataclass(frozen=True, slots=True)
class RestockRow:
    stock_item_id: UUID
    name: str
    # When the item's band last changed — what "recently" is ordered on. The
    # SPA renders it relative ("2 days ago"); the server sends the instant.
    changed_at: datetime
    is_essential: bool


@dataclass(frozen=True, slots=True)
class RestockRadarDto:
    recently_out: List[RestockRow] = field(default_factory=list)
    recently_low: List[RestockRow] = field(default_factory=list)


class GetRestockRadarHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self) -> RestockRadarDto:
        items: List[StockItem] = self.repository.get(StockItem).all()
        if not items:
            return RestockRadarDto()

        # Through the shared resolver, not `item.stock_level`: that
        # relationship is `lazy="noload"` and reading it returns None, which
        # reads as "no level recorded" — the trap `_level_access.py` closes.
        levels = resolve_levels_by_item(self.repository, items)

        out_rows: List[RestockRow] = []
        low_rows: List[RestockRow] = []
        for item in items:
            level = levels.get(item.id)
            if level is None or item.stock_level_last_updated is None:
                continue
            row = RestockRow(
                stock_item_id=item.id,
                name=item.name,
                changed_at=item.stock_level_last_updated,
                is_essential=bool(item.is_essential),
            )
            # `>=` on out, `==` on low: out is the terminal band and anything
            # beyond it is still out, while low is a single rung. Same
            # asymmetry `stock_status.is_out_of_stock` / `is_low_stock` use.
            if level.sequence >= OUT_OF_STOCK_SEQUENCE:
                out_rows.append(row)
            elif level.sequence == LOW_STOCK_SEQUENCE:
                low_rows.append(row)

        out_rows.sort(key=lambda r: r.changed_at, reverse=True)
        low_rows.sort(key=lambda r: r.changed_at, reverse=True)
        return RestockRadarDto(
            recently_out=out_rows[:MAX_PER_COLUMN],
            recently_low=low_rows[:MAX_PER_COLUMN],
        )


@DASHBOARD_ROUTER.route("/restock-radar", methods=["GET"])
def get_restock_radar():
    _Logger = logging.getLogger(__name__)
    _Result = GetRestockRadarHandler(SqlAlchemyRepository()).handle()
    _Logger.debug(
        "Restock radar: %d recently out, %d recently low",
        len(_Result.recently_out), len(_Result.recently_low),
    )
    return ok(_Result)
