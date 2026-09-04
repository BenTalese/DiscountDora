"""GET /api/dashboard/before-you-shop — what won't survive until the next shop.

The second of the two cards that replaced "Needs your attention" and "Dora
suggests" (owner, 2026-09-04). Same test as its sibling: it must answer a
question no other surface on the screen already answers.

The bell says "you are low on flour". The stock page says "you are low on
flour". Neither knows whether flour is **already on a list** — and that single
join is the difference between a nag you have already dealt with and a thing
you still have to do. So both halves of this card are filtered by list
membership, and what is left is, exactly, *the work outstanding before the
next shop*:

  running_out  items recorded low or out that are on no active list
  plan_gaps    items the coming fortnight's plan needs, that you haven't got,
               that are on no active list

`plan_gaps` is `gather_planned_demand` — the same signal the stock-item page's
planned-demand card and the planner read (R-003). It is not re-derived here;
this endpoint filters it and hands it over.

`shop_in_days` frames both: the nearest `planned_shop_date` on an active list.
None when no list carries one, in which case the card says "before your next
shop" rather than inventing a date.
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from uuid import UUID

from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import (LOW_STOCK_SEQUENCE,
                                          OUT_OF_STOCK_SEQUENCE)
from dora_api.features.app_settings.clock import household_today
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.features.stock_items._level_access import resolve_levels_by_item
from dora_api.features.stock_items.planned_demand import (URGENCY_NONE,
                                                          gather_planned_demand)
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

MAX_ROWS = 5


@dataclass(frozen=True, slots=True)
class RunningOutRow:
    stock_item_id: UUID
    name: str
    # 'low' | 'out' — the recorded band, not a belief. The inference overlay
    # (Zero-Input Pantry) is an opt-in and this card is not; promising "I think
    # you're out of this" on an install that never switched inference on would
    # be asserting something the household didn't ask Dora to guess.
    band: str
    is_essential: bool


@dataclass(frozen=True, slots=True)
class PlanGapRow:
    stock_item_id: UUID
    name: str
    # How many upcoming meals still need it once the cooked-batch pool is
    # accounted for — `PlannedDemand.needed_meals`, unmodified.
    needed_meals: int
    earliest_needed: Optional[date]
    recipe_names: List[str] = field(default_factory=list)
    # 'watch' (recorded low) | 'blocking' (recorded out).
    urgency: str = URGENCY_NONE


@dataclass(frozen=True, slots=True)
class BeforeYouShopDto:
    running_out: List[RunningOutRow] = field(default_factory=list)
    plan_gaps: List[PlanGapRow] = field(default_factory=list)
    # Days until the nearest planned shop date on an active list; None when no
    # active list names one. Negative is possible and meaningful — a planned
    # shop date that has passed and the list is still open.
    shop_in_days: Optional[int] = None


class GetBeforeYouShopHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self) -> BeforeYouShopDto:
        today = household_today(self.repository)
        active_lists = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS)
            .ne(SHOPPING_LIST_STATUS_DONE)
        )
        already_listed = self._items_on(active_lists)

        levels = self._recorded_levels()
        running_out = self._running_out(levels, already_listed)
        plan_gaps = self._plan_gaps(levels, already_listed)

        return BeforeYouShopDto(
            running_out=running_out,
            plan_gaps=plan_gaps,
            shop_in_days=self._shop_in_days(active_lists, today),
        )

    def _items_on(self, active_lists: List[ShoppingList]) -> set[UUID]:
        """Stock items with a line on any active list.

        Ticked lines count as listed: a ticked line means "in the trolley",
        which is the most dealt-with a thing can be. Only a *done* list drops
        out, and those are excluded above.
        """
        if not active_lists:
            return set()
        lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
            .in_([l.id for l in active_lists])
        )
        return {l.stock_item_id for l in lines if l.stock_item_id is not None}

    def _recorded_levels(self) -> dict[UUID, tuple[StockItem, int]]:
        """`{item_id: (item, recorded_sequence)}` for every tracked item.

        Resolved through the shared `resolve_levels_by_item` rather than off
        `item.stock_level`: that relationship is `lazy="noload"` and reading it
        returns None, which reads as "nobody recorded a level" — the trap
        `_level_access.py` exists to close.
        """
        items: List[StockItem] = self.repository.get(StockItem).all()
        if not items:
            return {}
        levels = resolve_levels_by_item(self.repository, items)
        out: dict[UUID, tuple[StockItem, int]] = {}
        for item in items:
            level = levels.get(item.id)
            if level is None:
                continue
            out[item.id] = (item, level.sequence)
        return out

    def _running_out(
        self,
        levels: dict[UUID, tuple[StockItem, int]],
        already_listed: set[UUID],
    ) -> List[RunningOutRow]:
        rows = [
            RunningOutRow(
                stock_item_id=item.id,
                name=item.name,
                band="out" if sequence >= OUT_OF_STOCK_SEQUENCE else "low",
                is_essential=bool(item.is_essential),
            )
            for item_id, (item, sequence) in levels.items()
            if sequence >= LOW_STOCK_SEQUENCE and item_id not in already_listed
        ]
        # Out before low, essentials before the rest within a band, then name.
        # Essentials rank inside the band rather than above it because an
        # essential you are merely low on is still less urgent than anything
        # you have actually run out of.
        rows.sort(key=lambda r: (r.band != "out", not r.is_essential, r.name.lower()))
        return rows[:MAX_ROWS]

    def _plan_gaps(
        self,
        levels: dict[UUID, tuple[StockItem, int]],
        already_listed: set[UUID],
    ) -> List[PlanGapRow]:
        recorded_by_item = {item_id: seq for item_id, (_, seq) in levels.items()}
        demand = gather_planned_demand(
            self.repository, recorded_by_item=recorded_by_item,
        )
        rows = []
        for item_id, d in demand.items():
            # `urgency` is already "the plan wants it AND you're low or out"
            # (`planned_demand.urgency_for`), so this is the whole filter —
            # re-testing the level here would be a second copy of that rule.
            if d.urgency == URGENCY_NONE or item_id in already_listed:
                continue
            entry = levels.get(item_id)
            if entry is None:
                continue
            rows.append(PlanGapRow(
                stock_item_id=item_id,
                name=entry[0].name,
                needed_meals=d.needed_meals,
                earliest_needed=d.earliest_needed,
                recipe_names=list(d.recipe_names),
                urgency=d.urgency,
            ))
        # Soonest-needed first; a gap with no date sorts last rather than
        # first, which `None` would otherwise do under a naive key.
        rows.sort(key=lambda r: (
            r.earliest_needed is None,
            r.earliest_needed or date.max,
            r.name.lower(),
        ))
        return rows[:MAX_ROWS]

    def _shop_in_days(
        self, active_lists: List[ShoppingList], today: date,
    ) -> Optional[int]:
        dates = [
            l.planned_shop_date for l in active_lists
            if l.planned_shop_date is not None
        ]
        if not dates:
            return None
        return (min(dates) - today).days


@DASHBOARD_ROUTER.route("/before-you-shop", methods=["GET"])
def get_before_you_shop():
    _Logger = logging.getLogger(__name__)
    _Result = GetBeforeYouShopHandler(SqlAlchemyRepository()).handle()
    _Logger.debug(
        "Before you shop: %d running out, %d plan gaps, shop in %s days",
        len(_Result.running_out), len(_Result.plan_gaps), _Result.shop_in_days,
    )
    return ok(_Result)
