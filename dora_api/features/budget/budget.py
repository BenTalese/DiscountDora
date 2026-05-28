"""P2-05 — grocery budget (cross-shopping-list).

  GET /api/budget/status    — current-period spend, remaining, projection
  GET /api/budget/history   — last N completed periods (default 6) for trend

Budget settings (amount + period) live on the User row and are managed via
the existing `PATCH /api/auth/me` endpoint. That keeps the wiring simple:
the SPA already refreshes the auth DTO whenever it patches the user, so
the dashboard / budget chip stay coherent without a second cache.

"Spent" in a period = the sum of every line on every archived shopping
list whose `completed_at` falls inside the rolling period, using the same
price-priority ladder the rest of the app uses:
  1. actual_unit_price  (user-entered, P2-02)
  2. picked_offer_price (offer snapshot at tick time)
  3. — skipped — no price means no contribution rather than a guess.

Cross-list by construction: every completed shop in the period counts,
no matter which list it was on.

"Projected" = same calculation but for active (non-archived) lists, using
the chosen offer's current price_now. Lets the dashboard show "if you
finish this shop you'll be at $X" without committing to numbers we can't
defend (offers can drift between now and finish).
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from flask import session

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.user import (BUDGET_PERIOD_MONTHLY,
                                           BUDGET_PERIOD_WEEKLY, User)
from dora_api.features.routers import BUDGET_ROUTER
from dora_api.infrastructure.api_response import ok, unauthorized
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ── Period boundaries ────────────────────────────────────────────────────
# Date-only arithmetic; the wall-clock "what week / month is it" question
# doesn't deserve timezone gymnastics for a personal-use app. The
# completed_at column is timezone-aware, so the comparison happens at
# datetime level using the start/end converted to UTC midnight.

def _period_bounds(today: date, period: str) -> tuple[date, date]:
    """Return [start, end) for the rolling period containing `today`.
    Week starts Monday (ISO weekday convention)."""
    if period == BUDGET_PERIOD_MONTHLY:
        start = today.replace(day=1)
        # First of next month — handles year rollover too.
        if start.month == 12:
            end = date(start.year + 1, 1, 1)
        else:
            end = date(start.year, start.month + 1, 1)
        return start, end
    # Default = weekly. Monday-start.
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    return start, end


def _as_utc_datetime(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


# ── Line-price ladder ────────────────────────────────────────────────────

def _price_paid_for(line: ShoppingListLine) -> float | None:
    """Captured price for an archived line. None when neither override
    nor snapshot is present (won't contribute to spend)."""
    if line.actual_unit_price is not None:
        return float(line.actual_unit_price)
    if line.picked_offer_price is not None:
        return float(line.picked_offer_price)
    return None


def _projected_price_for(
    line: ShoppingListLine,
    current_offer_lookup: dict[UUID, ProductOffer],
) -> float | None:
    """Price for a line on an active list, used only for the projected
    figure on the dashboard. Tries actual → snapshot → current offer of
    the selected product. Lines without any of those don't contribute."""
    direct = _price_paid_for(line)
    if direct is not None:
        return direct
    if line.selected_product_id and line.selected_product_id in current_offer_lookup:
        offer = current_offer_lookup[line.selected_product_id]
        if offer.price_now is not None:
            return float(offer.price_now)
    return None


# ── Status ───────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class BudgetStatusDto:
    enabled: bool
    amount: float | None
    period: str
    period_start: str | None
    period_end: str | None
    spent: float
    projected_active: float
    remaining: float | None
    over_budget: bool


class GetBudgetStatusHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, user_id: UUID) -> BudgetStatusDto | None:
        user: User | None = self.repository.get(User).by_id(user_id)
        if user is None:
            return None

        # Compute boundaries even when the feature is off — the dashboard
        # surfaces "this week's spend" as a passive figure for users who
        # haven't opted in.
        today = date.today()
        period = user.budget_period or BUDGET_PERIOD_WEEKLY
        start, end = _period_bounds(today, period)
        start_dt = _as_utc_datetime(start)
        end_dt = _as_utc_datetime(end)

        # Archived lists whose completed_at falls in the period. Lines on
        # those lists drive `spent`.
        archived = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(True)
            & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).gte(start_dt)
            & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).lt(end_dt)
        )
        archived_ids = [l.id for l in archived]

        # Active (non-archived) lists drive `projected_active`. Their
        # lines might pick up prices from the live ProductOffer rows.
        active = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(False)
        )
        active_ids = [l.id for l in active]

        # Bulk fetch lines for both sets.
        list_id_pool = archived_ids + active_ids
        lines: list[ShoppingListLine] = []
        if list_id_pool:
            lines = self.repository.get(ShoppingListLine).all(
                EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
                .in_(list_id_pool)
            )

        # Current offers for products selected on active lines — projection only.
        active_product_ids = list({
            l.selected_product_id for l in lines
            if l.shopping_list_id in active_ids and l.selected_product_id is not None
        })
        offer_lookup: dict[UUID, ProductOffer] = {}
        if active_product_ids:
            offers = self.repository.get(ProductOffer).all(
                EntityField(ProductOffer, "_product_id").in_(active_product_ids)
            )
            for offer in offers:
                # ProductOffer maps `_product_id` as the FK; the entity
                # exposes `product_id` indirectly via the table column,
                # so we look at the underscore-prefixed attribute the
                # mapping installs.
                pid = getattr(offer, "_product_id", None) or getattr(offer, "product_id", None)
                if pid is not None:
                    offer_lookup[pid] = offer

        archived_set = set(archived_ids)
        active_set = set(active_ids)

        spent = 0.0
        projected_active = 0.0
        for line in lines:
            qty = line.quantity if line.quantity is not None else 1
            if qty <= 0:
                continue
            if line.shopping_list_id in archived_set:
                price = _price_paid_for(line)
                if price is not None:
                    spent += price * qty
            elif line.shopping_list_id in active_set:
                price = _projected_price_for(line, offer_lookup)
                if price is not None:
                    projected_active += price * qty

        amount = (
            float(user.budget_amount)
            if user.budget_amount is not None and user.budget_amount > 0
            else None
        )
        remaining = (amount - spent) if amount is not None else None
        return BudgetStatusDto(
            enabled=amount is not None,
            amount=amount,
            period=period,
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            spent=round(spent, 2),
            projected_active=round(projected_active, 2),
            remaining=round(remaining, 2) if remaining is not None else None,
            over_budget=amount is not None and spent > amount,
        )


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


@BUDGET_ROUTER.route("/status", methods=["GET"])
def get_budget_status():
    _Logger = logging.getLogger(__name__)
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    dto = get_container().inject(GetBudgetStatusHandler).handle(user_id)
    if dto is None:
        return unauthorized()
    _Logger.debug(
        "budget status user=%s period=%s spent=%.2f remaining=%s",
        user_id, dto.period, dto.spent,
        f"{dto.remaining:.2f}" if dto.remaining is not None else "n/a",
    )
    return ok(dto)


# ── History ──────────────────────────────────────────────────────────────
# A small N-period look-back for the dashboard trend chip ("3 of your last
# 6 weeks went over"). Reuses the same line-walk; kept separate from
# /status so the dashboard's common case (just this week) stays cheap.

@dataclass(frozen=True, slots=True)
class BudgetHistoryRowDto:
    period_start: str
    period_end: str
    spent: float
    over_budget: bool


class GetBudgetHistoryHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, user_id: UUID, periods: int) -> list[BudgetHistoryRowDto] | None:
        user: User | None = self.repository.get(User).by_id(user_id)
        if user is None:
            return None

        today = date.today()
        period = user.budget_period or BUDGET_PERIOD_WEEKLY
        amount = (
            float(user.budget_amount)
            if user.budget_amount is not None and user.budget_amount > 0
            else None
        )

        # Walk back N periods. The current period is index 0; older
        # rows come from anchoring the boundary calculator to a date
        # in each earlier window.
        anchors: list[date] = []
        cursor = today
        for _ in range(periods):
            start, _end = _period_bounds(cursor, period)
            anchors.append(cursor)
            # One day before the period start lands inside the previous
            # period, regardless of week vs month.
            cursor = start - timedelta(days=1)

        # Earliest start covers the whole range — fetch archived lists
        # in one go and bucket by period.
        earliest_start, _ = _period_bounds(anchors[-1], period)
        latest_start, latest_end = _period_bounds(anchors[0], period)
        full_start_dt = _as_utc_datetime(earliest_start)
        full_end_dt = _as_utc_datetime(latest_end)

        archived = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(True)
            & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).gte(full_start_dt)
            & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).lt(full_end_dt)
        )
        archived_lookup: dict[UUID, ShoppingList] = {l.id: l for l in archived}
        lines: list[ShoppingListLine] = []
        if archived_lookup:
            lines = self.repository.get(ShoppingListLine).all(
                EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
                .in_(list(archived_lookup.keys()))
            )

        rows: list[BudgetHistoryRowDto] = []
        for anchor in anchors:
            start, end = _period_bounds(anchor, period)
            window_total = 0.0
            for line in lines:
                lst = archived_lookup.get(line.shopping_list_id)
                if lst is None or lst.completed_at is None:
                    continue
                completed_date = lst.completed_at.date()
                if completed_date < start or completed_date >= end:
                    continue
                qty = line.quantity if line.quantity is not None else 1
                if qty <= 0:
                    continue
                price = _price_paid_for(line)
                if price is not None:
                    window_total += price * qty
            rows.append(BudgetHistoryRowDto(
                period_start=start.isoformat(),
                period_end=end.isoformat(),
                spent=round(window_total, 2),
                over_budget=amount is not None and window_total > amount,
            ))
        return rows


@BUDGET_ROUTER.route("/history", methods=["GET"])
def get_budget_history():
    from flask import request
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    try:
        periods = int(request.args.get("periods", "6"))
    except (TypeError, ValueError):
        periods = 6
    # Clamp to a sensible spread — the SPA never needs hundreds of rows
    # and an open-ended N is an easy DoS surface.
    periods = max(1, min(periods, 26))
    rows = get_container().inject(GetBudgetHistoryHandler).handle(user_id, periods)
    if rows is None:
        return unauthorized()
    return ok({"rows": rows})
