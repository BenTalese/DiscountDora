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
from dora_api.domain.entities.meal_plan_reconcile_receipt import \
    MealPlanReconcileReceipt
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.entities.user import User
from dora_api.features.app_settings.access import money_features_enabled
from dora_api.features.app_settings.clock import household_today
from dora_api.features.budget.budget import GetBudgetStatusHandler
# The reconcile feature owns what "still pending" means and whether the
# household reconciles by hand; plan adherence reads both rather than
# re-deriving either.
from dora_api.features.meal_plans.reconcile import (_auto_drain_enabled,
                                                    _pending_states)
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
        # linking to /settings/money. Same shape as the buy verdict's gate
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

        # ── Plan adherence ────────────────────────────────────────
        # Of the meals planned inside the window whose day has passed, how many
        # are still unresolved on the reconcile queue.
        #
        # Both counts are window-scoped so the ratio compares like with like —
        # `reconcile_overdue_signal` counts the whole backlog, which is the
        # right number for an overdue *nudge* and the wrong one for a rate. The
        # definition of "pending" is not re-invented here: `_pending_states` +
        # `_auto_drain_enabled` are imported from the reconcile feature, so a
        # change to what counts as settled moves this score with it (R-003).
        manual_reconcile = not _auto_drain_enabled()
        past_planned_meals = 0
        unresolved_past_meals = 0
        if manual_reconcile:
            mpe_scheduled = EntityField(
                MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR,
            )
            past_entries: list[MealPlanEntry] = self.repository.get(MealPlanEntry).all(
                mpe_scheduled.gte(start.date()) & mpe_scheduled.lt(end.date())
            )
            past_planned_meals = len(past_entries)
            if past_entries:
                unresolved_past_meals = self._unresolved_among(
                    [e.id for e in past_entries]
                )

        return DoraScoreInputs(
            now=now,
            waste_event_count=waste_event_count,
            has_budget=has_budget,
            budget_over_pct=budget_over_pct,
            expired_item_count=expired_item_count,
            total_items_with_expiry=total_items_with_expiry,
            past_planned_meals=past_planned_meals,
            unresolved_past_meals=unresolved_past_meals,
            manual_reconcile=manual_reconcile,
            upcoming_planned_meals=upcoming_planned_meals,
            upcoming_cookable_meals=upcoming_cookable_meals,
            money_enabled=money_enabled,
        )

    def _unresolved_among(self, entry_ids: list[UUID]) -> int:
        """How many of these entries' *latest* receipts are still pending.

        Latest-per-entry, not any-receipt: an entry that was disputed and then
        settled has two receipts, and counting the old one would keep it
        unresolved forever. The `(created_at, id)` ordering matches
        `_latest_receipt` in the reconcile feature (FU-529), so both surfaces
        agree on which receipt is current.

        An entry with **no** receipt at all is not counted: the sweep writes
        one when the day passes, so no receipt means the sweep hasn't run for
        that day yet — Dora's lag, not the household's.
        """
        pending = set(_pending_states(_auto_drain_enabled()))
        receipts: list[MealPlanReconcileReceipt] = self.repository.get(
            MealPlanReconcileReceipt
        ).all(
            EntityField(
                MealPlanReconcileReceipt,
                MealPlanReconcileReceipt.Fields.MEAL_PLAN_ENTRY_ID,
            ).in_(entry_ids)
        )
        latest: dict[UUID, MealPlanReconcileReceipt] = {}
        for receipt in receipts:
            current = latest.get(receipt.meal_plan_entry_id)
            if current is None or (receipt.created_at, str(receipt.id)) > (
                current.created_at, str(current.id)
            ):
                latest[receipt.meal_plan_entry_id] = receipt
        return sum(1 for r in latest.values() if r.state in pending)


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
