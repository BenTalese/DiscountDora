"""GET /api/dashboard/lists — the three shopping lists worth a shortcut.

Owner feedback, 2026-09-04: *"What's the point of the shopping list widget?
Also it says primary on it which indicates to me it's from a long time ago …
I think seeing my current shopping list +1 nearest future, +1 most recent
finished as more useful as quick nav to them with some quick data shown on
them like total items, spend amount (if money on)."*

He is right about the provenance. The old card was built when the interesting
fact about a list was that it was the *cart button's target*, so it rendered
one list, labelled "Primary shopping list", and fetched a whole
`ShoppingListDetail` — every line, every offer, every resolved store — to show
three numbers off its `totals`.

Three picks, each a different tense:

  current   the list in flight: a `shopping` list first, else the soonest
            draft. This is the one you are holding in the supermarket.
  next      the next dated draft after `current` — "the big shop on Saturday".
  finished  the most recently completed list, which is how you answer "did I
            already buy that?" without leaving the dashboard.

Picking is server-side because "which list is current" is a cross-entity rule
over status and three different date fields (`effective_date` already resolves
that precedence, and is the entity's own property — R-003). The totals come
from `compute_list_totals`, the same authority the list detail uses, so the
dashboard can never disagree with the page it links to.
"""
import logging
from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from uuid import UUID

from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList)
from dora_api.features.app_settings.clock import household_today
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.features.shopping_lists.get_shopping_list_detail import \
    GetShoppingListDetailHandler
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class DashboardListCard:
    shopping_list_id: UUID
    display_name: str
    status: str
    # Where the list sits in time — `ShoppingList.effective_date`, which
    # already encodes the completed > planned > created precedence.
    effective_date: date
    line_count: int
    unticked_count: int
    # Money travels always; the *card* is what gates it on the money opt-in,
    # exactly as the shopping-list page does. Gating the payload instead would
    # mean two shapes for one endpoint and a card that can't be switched on
    # without a round trip.
    total_price: float
    remaining_price: float
    total_savings: float


@dataclass(frozen=True, slots=True)
class DashboardListsDto:
    current: Optional[DashboardListCard] = None
    next: Optional[DashboardListCard] = None
    finished: Optional[DashboardListCard] = None


class GetDashboardListsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self) -> DashboardListsDto:
        today = household_today(self.repository)
        status_field = EntityField(ShoppingList, ShoppingList.Fields.STATUS)

        active = self.repository.get(ShoppingList).all(
            status_field.ne(SHOPPING_LIST_STATUS_DONE)
        )
        done = self.repository.get(ShoppingList).all(
            status_field.eq(SHOPPING_LIST_STATUS_DONE)
        )

        current = self._pick_current(active, today)
        nxt = self._pick_next(active, current)
        # Most recently finished. `effective_date` is `completed_at` for a done
        # list, so this is "the last shop", not "the last list created".
        finished = max(done, key=lambda l: l.effective_date, default=None)

        return DashboardListsDto(
            current=self._card(current),
            next=self._card(nxt),
            finished=self._card(finished),
        )

    def _pick_current(
        self, active: List[ShoppingList], today: date,
    ) -> Optional[ShoppingList]:
        """The list you are shopping, or about to.

        A `shopping` list wins outright — somebody pressed Start shopping, and
        no draft outranks that. Otherwise the draft whose date is nearest,
        preferring one that is due (today or overdue) over one still ahead:
        a shop you meant to do on Tuesday is more "current" on Thursday than
        one planned for Saturday.
        """
        shopping = [l for l in active if l.is_shopping]
        if shopping:
            return min(shopping, key=lambda l: l.effective_date)
        if not active:
            return None
        return min(
            active,
            key=lambda l: (
                l.effective_date > today,
                abs((l.effective_date - today).days),
                l.effective_date,
            ),
        )

    def _pick_next(
        self, active: List[ShoppingList], current: Optional[ShoppingList],
    ) -> Optional[ShoppingList]:
        """The nearest active list *after* `current` — the owner's "+1 nearest
        future".

        Strictly after, by date: a second list sharing `current`'s date is not
        the next shop, it is a duplicate of this one, and showing it as "next"
        would be the card asserting a sequence that doesn't exist. Ties on date
        are broken by id so the pick can't swap places between loads — the same
        stability the insight cards keep.
        """
        if current is None:
            return None
        later = [
            l for l in active
            if l.id != current.id and l.effective_date > current.effective_date
        ]
        if not later:
            return None
        return min(later, key=lambda l: (l.effective_date, str(l.id)))

    def _card(self, lst: Optional[ShoppingList]) -> Optional[DashboardListCard]:
        if lst is None:
            return None
        # One detail load per card, at most three. The card this replaces
        # already did one, and the totals authority takes hydrated line DTOs —
        # re-deriving them here would put a second money ladder in a second
        # place, which is the whole reason `compute_list_totals` exists.
        detail = GetShoppingListDetailHandler(self.repository).handle(lst.id)
        if detail is None:
            return None
        t = detail.totals
        return DashboardListCard(
            shopping_list_id=lst.id,
            display_name=lst.display_name,
            status=lst.status,
            effective_date=lst.effective_date,
            line_count=t.line_count,
            unticked_count=t.unticked_count,
            total_price=t.total_price,
            remaining_price=t.remaining_price,
            total_savings=t.total_savings,
        )


@DASHBOARD_ROUTER.route("/lists", methods=["GET"])
def get_dashboard_lists():
    _Logger = logging.getLogger(__name__)
    _Result = GetDashboardListsHandler(SqlAlchemyRepository()).handle()
    _Logger.debug(
        "Dashboard lists: current=%s next=%s finished=%s",
        _Result.current.display_name if _Result.current else None,
        _Result.next.display_name if _Result.next else None,
        _Result.finished.display_name if _Result.finished else None,
    )
    return ok(_Result)
