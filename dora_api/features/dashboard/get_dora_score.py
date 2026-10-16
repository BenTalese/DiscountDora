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
from datetime import datetime, timedelta, timezone
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
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.features.app_settings.access import money_features_enabled
from dora_api.features.app_settings.clock import household_today
from dora_api.features.budget.budget import GetBudgetStatusHandler
from dora_api.features.recipes.get_recipes import load_recipe_cookability
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

        # ── Plan coverage ─────────────────────────────────────────
        # Of the meals planned for the next 7 days, how many the pantry can
        # cook right now. Deliberately forward-looking and therefore identical
        # in both windows — see `_score_plan_coverage` for why that is the
        # accepted trade.
        #
        # ⚠️ **This runs first, and it has to.** `load_recipe_cookability`
        # eager-loads `RecipeIngredient → StockItem → StockLevel`, and
        # `StockItem.stock_level` is `lazy="noload"`. If anything has already
        # pulled those StockItem rows into the session — and the Freshness
        # block below does exactly that, with a bare `get(StockItem).all()` —
        # the identity map hands back the cached instances and the eager load
        # silently does not populate `stock_level`. Every linked ingredient
        # then looks unstocked, so `missing_count` is non-zero for every
        # recipe and coverage scores 0.
        #
        # That is the same trap `_level_access.py` was written for (R-032), and
        # it is invisible: the endpoint returns 200 and the card renders a
        # confident, wrong number. Found in the 2026-09-04 browser walk, where
        # the card claimed "None of your 6 planned meals can be cooked right
        # now" beside a Next-to-cook card offering to cook five of them.
        #
        # Cookability comes from the shared map (R-003), the same one the
        # dashboard summary's per-entry `missing_count` reads. An entry whose
        # recipe has unlinked ingredients or no ingredients at all is excluded
        # from both counts: its cookability is genuinely unknown, and scoring
        # "unknown" as "can't" would mark a household down for not having
        # linked its recipes yet.
        upcoming_planned_meals = 0
        upcoming_cookable_meals = 0
        if not lagged:
            cookability = load_recipe_cookability(self.repository)
            today = household_today(self.repository)
            week_ahead = today + timedelta(days=7)
            mpe_scheduled = EntityField(
                MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR,
            )
            upcoming: list[MealPlanEntry] = (
                self.repository.get(MealPlanEntry)
                .include(MealPlanEntry.Fields.RECIPE)
                .all(mpe_scheduled.between(today, week_ahead))
            )
            for entry in upcoming:
                missing, ingredient_count, unlinked = cookability.get(
                    entry.recipe.id, (0, 0, 0)
                )
                if ingredient_count == 0 or unlinked > 0:
                    continue
                upcoming_planned_meals += 1
                if missing == 0:
                    upcoming_cookable_meals += 1

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
        #
        # FU-823 / R-058 — and skip it entirely when money features are off.
        # `GetBudgetStatusHandler` deliberately computes period boundaries
        # *even when the feature is off* (see budget.py) so the dashboard can
        # show a passive "spent this week" figure — which means it happily
        # returns a live budget for a money-off install. Calling it
        # unconditionally here meant the composite was weighted by money data
        # the household had opted out of, and the card rendered a Budget row
        # linking to /settings/budget. Same shape as the buy verdict's gate
        # (`get_buy_verdict.py`, ADR-055): the reasoning is gated at the
        # gather, not just suppressed at the render.
        money_enabled = money_features_enabled(self.repository)
        has_budget = False
        budget_over_pct: float | None = None
        if money_enabled and not lagged:
            budget = GetBudgetStatusHandler(self.repository).handle()
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

        # The unplanned-run-out and stocktake gathers were removed with their
        # components (owner review, 2026-09-04 — see the note on
        # `DoraScoreComponentKey`). Both cost a query and a scan on every
        # dashboard load for a signal that graded how diligently the app was
        # used rather than how the kitchen was doing. `ConsumptionEvent` keeps
        # its other readers (pantry belief, the stock-item history); nothing is
        # orphaned by this.

        return DoraScoreInputs(
            now=now,
            waste_event_count=waste_event_count,
            has_budget=has_budget,
            budget_over_pct=budget_over_pct,
            expired_item_count=expired_item_count,
            total_items_with_expiry=total_items_with_expiry,
            upcoming_planned_meals=upcoming_planned_meals,
            upcoming_cookable_meals=upcoming_cookable_meals,
            money_enabled=money_enabled,
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
