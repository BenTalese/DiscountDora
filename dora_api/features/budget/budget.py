"""P2-05 — grocery budget (cross-shopping-list).

  GET /api/budget/status    — current-period spend, remaining, projection
  GET /api/budget/history   — last N completed periods (default 6) for trend

Budget settings (amount + period) are a single install-wide household value
on `AppSetting` (spend is summed across every *shared* shopping list, so the
target must be shared too). Any household member edits them via
`PATCH /api/budget/settings`; clients read them via `/api/health.budget_policy`.
Value-driven: `budget_amount` NULL/≤0 ⇒ the feature is off.

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

**Shared arithmetic** — `period_bounds(today, period)`, `period_spent(...)`,
and `period_headroom(on_date, repository)` are the only functions authorised
to compute budget windows and remaining-money figures. The trim-to-budget
optimiser (FU-448) and any future budget-aware surface call `period_headroom`
rather than re-deriving it in a second place. R-003 state-ownership.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.app_settings.clock import household_today
from dora_api.domain.entities.app_setting import (ALLOWED_BUDGET_PERIODS,
                                                  AppSetting,
                                                  BUDGET_PERIOD_MONTHLY,
                                                  BUDGET_PERIOD_WEEKLY)
from dora_api.features.routers import BUDGET_ROUTER
from dora_api.features.shopping_lists._line_price import line_paid_unit_price
from dora_api.infrastructure.api_response import bad_request, ok, unauthorized
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# ── Period boundaries ────────────────────────────────────────────────────
# Date-only arithmetic; the wall-clock "what week / month is it" question
# doesn't deserve timezone gymnastics for a personal-use app. The
# completed_at column is timezone-aware, so the comparison happens at
# datetime level using the start/end converted to UTC midnight.

def period_bounds(today: date, period: str) -> tuple[date, date]:
    """Return [start, end) for the rolling period containing `today`.
    Week starts Monday (ISO weekday convention). Exported so the
    trim-to-budget optimiser can compute headroom for a shop scheduled
    in a later period."""
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


def _budget_amount(setting: AppSetting) -> float | None:
    """Positive household budget_amount as a float, or None when off / unset."""
    if setting.budget_amount is not None and setting.budget_amount > 0:
        return float(setting.budget_amount)
    return None


def _budget_period(setting: AppSetting) -> str:
    """The household budget period, defaulting to weekly if unset."""
    return setting.budget_period or BUDGET_PERIOD_WEEKLY


def period_spent(
    period_start: date,
    period_end: date,
    repository: SqlAlchemyRepository,
) -> float:
    """Sum of archived shopping-list lines whose completed_at falls in the
    half-open window `[period_start, period_end)`. Uses the `_line_price`
    ladder — actual > picked-offer > drop. Household-wide by construction
    (the schema is single-household): every completed shop in the period
    counts, no matter which list or user it was on.

    Only **ticked** lines count. A price on a line is not evidence it was
    bought: `picked_offer_price` is snapshotted when the line is *added*, so
    an unticked line with a linked offer carries a price it never cost. Left
    unfiltered, finishing a list with leftovers billed the whole list to the
    budget and inflated `period_headroom` by the same amount. This mirrors
    `compute_list_totals`' `spent_only` rule, which a done list's own receipt
    has always applied."""
    start_dt = _as_utc_datetime(period_start)
    end_dt = _as_utc_datetime(period_end)
    archived = repository.get(ShoppingList).all(
        EntityField(ShoppingList, ShoppingList.Fields.STATUS).eq(SHOPPING_LIST_STATUS_DONE)
        & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).gte(start_dt)
        & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).lt(end_dt)
    )
    if not archived:
        return 0.0
    archived_ids = [l.id for l in archived]
    lines = repository.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
        .in_(archived_ids)
        & EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(True)
        & EntityField(ShoppingListLine, ShoppingListLine.Fields.DEFERRED_BY_BUDGET).eq(False)
    )
    total = 0.0
    for line in lines:
        qty = line.quantity if line.quantity is not None else 1
        if qty <= 0:
            continue
        price = line_paid_unit_price(line)
        if price is not None:
            total += price * qty
    return total


def period_headroom(
    on_date: date,
    repository: SqlAlchemyRepository,
) -> float | None:
    """The trim-to-budget optimiser's single source of truth for "how much
    money is left in the household budget for a shop dated `on_date`".
    Returns None when there's no positive household budget (nothing to
    constrain against). When the shop is scheduled for a future period, we
    return the *full* budget_amount for that period — no spend has landed
    yet. When it's in the current or past period, we deduct actual spend so
    far in that window."""
    setting = get_or_create_app_setting(repository)
    amount = _budget_amount(setting)
    if amount is None:
        return None
    start, end = period_bounds(on_date, _budget_period(setting))
    spent = period_spent(start, end, repository)
    return amount - spent


# ── Line-price ladder ────────────────────────────────────────────────────
# The actual→picked ladder lives in `shopping_lists._line_price`
# (`line_paid_unit_price`, K2 extract). Budget's projection adds one more
# rung (the selected product's *current* offer) on top of it.


def projected_unit_price(
    line: ShoppingListLine,
    current_offer_lookup: dict[UUID, ProductOffer],
) -> float | None:
    """Price for a line on an active list. Tries actual → snapshot →
    current offer of the selected product. Lines without any of those
    don't contribute. Public — the trim-to-budget optimiser reads the
    same ladder so the projected figure it constrains against matches
    the dashboard's projection to the cent."""
    direct = line_paid_unit_price(line)
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
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self) -> BudgetStatusDto | None:
        setting = get_or_create_app_setting(self.repository)

        # Compute boundaries even when the feature is off — the dashboard
        # surfaces "this week's spend" as a passive figure even when no
        # budget is set. R-021 — week/month windows align to the household
        # calendar boundary, not server-local.
        today = household_today(self.repository)
        period = _budget_period(setting)
        start, end = period_bounds(today, period)

        # Spent = archived lines in the window. Extracted to the shared
        # `period_spent` helper so the trim-to-budget optimiser reads the
        # same number.
        spent = period_spent(start, end, self.repository)

        # Projected still lives here — dashboard-only. Walks active lists'
        # lines, adding one more rung (current offer of the selected
        # product) beyond the archived ladder.
        active = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
        )
        active_ids = [l.id for l in active]
        active_lines: list[ShoppingListLine] = []
        if active_ids:
            active_lines = self.repository.get(ShoppingListLine).all(
                EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
                .in_(active_ids)
            )

        active_product_ids = list({
            l.selected_product_id for l in active_lines
            if l.selected_product_id is not None
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

        projected_active = 0.0
        for line in active_lines:
            qty = line.quantity if line.quantity is not None else 1
            if qty <= 0:
                continue
            price = projected_unit_price(line, offer_lookup)
            if price is not None:
                projected_active += price * qty

        amount = _budget_amount(setting)
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
    dto = GetBudgetStatusHandler(SqlAlchemyRepository()).handle()
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
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, periods: int) -> list[BudgetHistoryRowDto] | None:
        setting = get_or_create_app_setting(self.repository)

        # R-021 — current period anchored on household-tz today.
        today = household_today(self.repository)
        period = _budget_period(setting)
        amount = _budget_amount(setting)

        # Walk back N periods. The current period is index 0; older
        # rows come from anchoring the boundary calculator to a date
        # in each earlier window.
        anchors: list[date] = []
        cursor = today
        for _ in range(periods):
            start, _end = period_bounds(cursor, period)
            anchors.append(cursor)
            # One day before the period start lands inside the previous
            # period, regardless of week vs month.
            cursor = start - timedelta(days=1)

        # Earliest start covers the whole range — fetch archived lists
        # in one go and bucket by period.
        earliest_start, _ = period_bounds(anchors[-1], period)
        latest_start, latest_end = period_bounds(anchors[0], period)
        full_start_dt = _as_utc_datetime(earliest_start)
        full_end_dt = _as_utc_datetime(latest_end)

        archived = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.STATUS).eq(SHOPPING_LIST_STATUS_DONE)
            & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).gte(full_start_dt)
            & EntityField(ShoppingList, ShoppingList.Fields.COMPLETED_AT).lt(full_end_dt)
        )
        archived_lookup: dict[UUID, ShoppingList] = {l.id: l for l in archived}
        lines: list[ShoppingListLine] = []
        if archived_lookup:
            # Ticked-only, for the same reason as `period_spent` — history and
            # the current period must agree on what "spent" means.
            lines = self.repository.get(ShoppingListLine).all(
                EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
                .in_(list(archived_lookup.keys()))
                & EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(True)
                & EntityField(ShoppingListLine, ShoppingListLine.Fields.DEFERRED_BY_BUDGET).eq(False)
            )

        rows: list[BudgetHistoryRowDto] = []
        for anchor in anchors:
            start, end = period_bounds(anchor, period)
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
                price = line_paid_unit_price(line)
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
    rows = GetBudgetHistoryHandler(SqlAlchemyRepository()).handle(periods)
    if rows is None:
        return unauthorized()
    return ok({"rows": rows})


# ── Settings (household budget) ────────────────────────────────────────────
# The budget amount + period are an install-wide household value on
# AppSetting (moved off User — spend is shared, so the target must be too).
# Unlike the rest of AppSetting (admin-only PATCH /app-settings), this is
# editable by ANY authenticated household member: the grocery budget is
# kitchen-setup-grade shared config, same access class as shared shopping
# lists / stores / stock locations that any member curates. Value-driven —
# an amount of null / 0 clears the budget (no separate enabled flag).

class UpdateBudgetSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Present-in-body semantics: send `amount` (incl. explicit null / 0) to set
    # it, omit to leave unchanged. 0 or null ⇒ budget off.
    amount: float | None = Field(default=None, ge=0)
    period: str | None = None


@dataclass(frozen=True, slots=True)
class BudgetSettingsDto:
    amount: float | None
    period: str


@BUDGET_ROUTER.route("/settings", methods=["PATCH"])
@has_request_body(UpdateBudgetSettingsRequest)
def update_budget_settings():
    _Logger = logging.getLogger(__name__)
    if _current_user_id() is None:
        return unauthorized()
    request: UpdateBudgetSettingsRequest = get_request_body()
    set_fields = request.model_fields_set

    if "period" in set_fields and request.period is not None:
        if request.period not in ALLOWED_BUDGET_PERIODS:
            return bad_request(
                "Invalid budget period.",
                detail=f"'{request.period}' is not a valid budget period "
                       f"(expected one of {list(ALLOWED_BUDGET_PERIODS)}).",
            )

    repository = SqlAlchemyRepository()
    setting = get_or_create_app_setting(repository)
    if "amount" in set_fields:
        # Value-driven: 0 / null clears the budget (feature off).
        setting.budget_amount = (
            float(request.amount)
            if request.amount is not None and request.amount > 0
            else None
        )
    if "period" in set_fields and request.period is not None:
        setting.budget_period = request.period
    repository.save_changes()

    _Logger.info(
        "Household budget updated (amount=%s period=%s).",
        setting.budget_amount, setting.budget_period,
    )
    return ok(BudgetSettingsDto(
        amount=float(setting.budget_amount) if setting.budget_amount else None,
        period=setting.budget_period or BUDGET_PERIOD_WEEKLY,
    ))
