"""P8-08 — GET /api/dashboard/dora-score.

Assembles the raw inputs for the score (:mod:`dora_api.domain.dora_score`),
delegates to ``compute_score`` twice (current window + 7-day-lagged
window for the trend arrow), and returns the composite DTO the SPA
renders as the dashboard's kitchen-health card.

Every "does this signal apply to this household?" call lives here —
the domain core doesn't know what a StockItem is; the handler does.
Same R-027 split as :mod:`pantry_belief` and :mod:`buy_verdict`. All
inputs are gathered against a single ``datetime.now()`` snapshot so
the current + lagged windows line up exactly.

Placement (per user 2026-07-04): a new endpoint under the dashboard
router — the score is a dashboard component, not general-purpose
reporting. A future assistant tool can call this endpoint directly
if it ever wants to answer "how's the kitchen doing?" honestly.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from flask import session

from dora_api.domain.dora_score import (
    DoraScoreDto,
    DoraScoreInputs,
    compose_with_trend,
    compute_score,
    lagged_window_end,
    lagged_window_start,
    window_start,
)
from dora_api.domain.entities.consumption_event import ConsumptionEvent
from dora_api.domain.entities.shopping_list import (
    ShoppingList,
    ShoppingListLine,
    SHOPPING_LIST_STATUS_DONE,
)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.entities.user import User
from dora_api.domain.stock_status import OUT_OF_STOCK_SEQUENCE
from dora_api.features.budget.budget import GetBudgetStatusHandler
from dora_api.features.routers import DASHBOARD_ROUTER
from dora_api.infrastructure.api_response import ok, unauthorized
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


_LOGGER = logging.getLogger(__name__)


class GetDoraScoreHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, user_id: UUID) -> DoraScoreDto:
        # Snapshot the wall clock once — every window boundary and
        # every "in the last 30 days" filter uses this exact moment,
        # so the current and lagged windows can't drift apart on a
        # slow query.
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        current_inputs = self._gather_inputs(user_id, now, lagged=False)
        current = compute_score(current_inputs)

        # Skip the lagged compute when the composite doesn't exist —
        # a brand-new install has no trend, and the lagged pass would
        # just re-scan empty windows.
        if current.composite is None:
            return current

        lagged_inputs = self._gather_inputs(user_id, now, lagged=True)
        lagged = compute_score(lagged_inputs)
        return compose_with_trend(current, lagged)

    def _gather_inputs(
        self,
        user_id: UUID,
        now: datetime,
        lagged: bool,
    ) -> DoraScoreInputs:
        if lagged:
            start = lagged_window_start(now)
            end = lagged_window_end(now)
        else:
            start = window_start(now)
            end = now

        # ── Waste ──────────────────────────────────────────────────
        waste_field = EntityField(
            StockItemWasteEvent,
            StockItemWasteEvent.Fields.OCCURRED_AT,
        )
        waste_event_count = self.repository.get(StockItemWasteEvent).count(
            waste_field.gte(start) & waste_field.lt(end)
        )

        # ── Budget ────────────────────────────────────────────────
        # Reuse the existing status handler — same period boundaries,
        # same price-ladder rules, no reimplementation. The lagged
        # window doesn't cleanly map onto a budget "period" (weeks /
        # months don't slide with our 30d), so we ONLY score budget on
        # the current window. For the lagged pass we mark budget as
        # dormant (score=None) so it doesn't drag or lift the trend
        # arrow — trend should reflect the *loop* signals, not a
        # calendar boundary crossing.
        has_budget = False
        budget_over_pct: float | None = None
        if not lagged:
            budget = GetBudgetStatusHandler(SqlAlchemyRepository()).handle(user_id)
            if budget is not None and budget.amount is not None and budget.enabled:
                has_budget = True
                if budget.amount > 0:
                    budget_over_pct = (budget.spent / budget.amount) - 1.0

        # ── Freshness ─────────────────────────────────────────────
        # Total items with an expiry_date set. Expired = expiry_date
        # on-or-before the window's *end* (i.e. as of "now" for the
        # current window, or as of 7d ago for the lagged window).
        as_of = end.date()
        stock_items: list[StockItem] = self.repository.get(StockItem).all()
        total_items_with_expiry = sum(1 for s in stock_items if s.expiry_date is not None)
        expired_item_count = sum(
            1 for s in stock_items
            if s.expiry_date is not None and s.expiry_date <= as_of
        )

        # ── Unplanned run-outs ────────────────────────────────────
        # Every ConsumptionEvent in the window that landed the item
        # AT OUT_OF_STOCK (to_sequence == 2). "Unplanned" = no
        # ShoppingListLine on an *active* (not-done) list for that
        # stock_item at the moment the event happened.
        ce_occurred_at = EntityField(
            ConsumptionEvent, ConsumptionEvent.Fields.OCCURRED_AT,
        )
        ce_to_seq = EntityField(
            ConsumptionEvent, ConsumptionEvent.Fields.TO_SEQUENCE,
        )
        runout_events: list[ConsumptionEvent] = self.repository.get(ConsumptionEvent).all(
            ce_occurred_at.gte(start)
            & ce_occurred_at.lt(end)
            & ce_to_seq.eq(OUT_OF_STOCK_SEQUENCE)
        )
        unplanned_runout_count = 0
        if runout_events:
            # Bulk-fetch the active-list line coverage set: every
            # (stock_item_id) that has a line on any non-done list.
            # Simpler than a per-event date-scoped query and honest
            # enough — if you have the item on any active list, that
            # counts as "planned". The false-positive rate (an item
            # on a done list from months ago) is captured by the
            # list-status filter.
            active_lists: list[ShoppingList] = self.repository.get(ShoppingList).all(
                EntityField(ShoppingList, ShoppingList.Fields.STATUS)
                .ne(SHOPPING_LIST_STATUS_DONE)
            )
            active_list_ids = [l.id for l in active_lists]
            planned_stock_item_ids: set[UUID] = set()
            if active_list_ids:
                lines: list[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
                    EntityField(
                        ShoppingListLine,
                        ShoppingListLine.Fields.SHOPPING_LIST_ID,
                    ).in_(active_list_ids)
                )
                planned_stock_item_ids = {
                    l.stock_item_id for l in lines if l.stock_item_id is not None
                }
            for event in runout_events:
                if event.stock_item_id is None:
                    # Denormalised event whose FK went away (SET NULL
                    # on stock-item delete). Count as unplanned — the
                    # user did run out, we just can't check coverage.
                    unplanned_runout_count += 1
                elif event.stock_item_id not in planned_stock_item_ids:
                    unplanned_runout_count += 1

        # ── Stocktake ─────────────────────────────────────────────
        # % of stock items whose last_checked_at falls inside the
        # window. Fresh installs (total==0) → excluded upstream.
        total_stock_items = len(stock_items)
        items_checked_in_window = sum(
            1 for s in stock_items
            if s.last_checked_at is not None
            and start <= s.last_checked_at < end
        )

        return DoraScoreInputs(
            now=now,
            waste_event_count=waste_event_count,
            has_budget=has_budget,
            budget_over_pct=budget_over_pct,
            expired_item_count=expired_item_count,
            total_items_with_expiry=total_items_with_expiry,
            unplanned_runout_count=unplanned_runout_count,
            items_checked_in_window=items_checked_in_window,
            total_stock_items=total_stock_items,
        )


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


@DASHBOARD_ROUTER.route("/dora-score", methods=["GET"])
def get_dora_score():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    dto = GetDoraScoreHandler(SqlAlchemyRepository()).handle(user_id)
    _LOGGER.info(
        "Dora Score user=%s composite=%s trend=%s (delta=%s)",
        user_id,
        dto.composite,
        dto.trend_direction,
        dto.trend_delta,
    )
    return ok(dto)
