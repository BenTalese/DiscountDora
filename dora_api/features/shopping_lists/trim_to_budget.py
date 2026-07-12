"""FU-448 — Trim-to-budget optimiser (PROPOSAL_BUDGET_AWARE_LISTS).

  POST /api/shopping-lists/<list_id>/trim-to-budget

Two modes on one endpoint:

- `preview`: classify every active line against the five-tier stack in
  brief §4, pick cuts until projected ≤ budget headroom (or we exhaust
  cuttable lines), return the plan. No mutation.
- `apply`:  run the same pass then flip `deferred_by_budget=True` on
  the cuts. Idempotent — running twice with the same inputs yields the
  same set (deterministic classification).

The reason-chip vocabulary is fixed (brief §5). Chips render on read
from the same classification (Step 4 lands the read-path derivation).
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.recipe import Recipe
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine,
                                                    ADDED_VIA_AUTO_FREQUENTLY_ADDED,
                                                    ADDED_VIA_AUTO_LOW_STOCK,
                                                    ADDED_VIA_AUTO_MEAL_PLAN,
                                                    ADDED_VIA_AUTO_RECIPE)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.user import User
from dora_api.features.app_settings.clock import household_today
from dora_api.features.auth.register_user import SESSION_USER_ID_KEY
from dora_api.features.budget.budget import (projected_unit_price,
                                             period_headroom)
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.shopping_lists._line_price import line_paid_unit_price
from dora_api.domain.stock_status import is_low_stock, is_out_of_stock
from dora_api.features.stock_items.get_buy_verdict import (BuyVerdictDto,
                                                           _gather_inputs,
                                                           compose_verdict)
from dora_api.infrastructure.api_response import not_found, ok, unauthorized
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import (get_request_body)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


_LOGGER = logging.getLogger(__name__)


# ── Reason chip vocabulary (brief §5) ─────────────────────────────────
# Fixed set. If a classification path can't produce one of these, the
# line isn't a candidate.

REASON_HABIT_CAN_WAIT       = "Habit — can wait"
REASON_COVER_LEFT           = "{n} days' cover left"          # N filled in
REASON_NOT_URGENT           = "Not urgent"
REASON_ABOVE_USUAL_PRICE    = "Above your usual price"
REASON_OUT_NO_MEAL          = "Out, but no meal booked"
REASON_FOR_RECIPE_ON_DAY    = "For {recipe} on {day}"
REASON_NEEDED_FOR_N_MEALS   = "Needed for {n} meals later"


# ── Tunables (brief §4) ───────────────────────────────────────────────
# Kept as module constants so tests can monkey-patch and future tuning
# doesn't hunt through the classifier logic.

NEAR_TERM_DEMAND_DAYS       = 2     # never-cut window for meal-plan demand
SHORT_TERM_DEMAND_DAYS      = 7     # tier-1/2/4 "no demand in next 7 days"
BUY_VERDICT_DEMAND_DAYS     = 3     # tier-3 "no demand in next 3 days"
FAR_OUT_MIN_DAYS            = 5     # tier-5 "scheduled ≥ 5 days out"
TIER_2_MIN_COVER_DAYS       = 5     # tier-2 "≥ 5 days of cover"
MIN_LINE_VALUE              = 2.00  # never-cut lines below this (not worth the chip)


# ── Request / response DTOs ───────────────────────────────────────────


class TrimToBudgetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = Field(default="preview")  # "preview" | "apply"
    # Optional override of the target budget. None → period-remaining, as
    # computed by `period_headroom(user, on_date)`. Callers who want a
    # one-off ("keep this shop under $X") pass an explicit target.
    budget_target: float | None = Field(default=None, ge=0)
    # Line IDs the user has explicitly excluded from the trim (see brief
    # §6.2 "Keep" button on the preview). Never cut, even if their tier
    # would say otherwise.
    exclude_line_ids: List[UUID] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class TrimmedLineDto:
    line_id: UUID
    tier: int
    reason_chip: str
    saved: float


@dataclass(frozen=True, slots=True)
class TrimToBudgetResponse:
    projected_total: float
    budget_target: float | None    # None = budget disabled → nothing to trim
    overshoot: float               # 0 when we're already under budget
    trimmed: List[TrimmedLineDto]
    still_over: float              # >0 when we ran out of safe cuts
    applied: bool


# ── Classification context ────────────────────────────────────────────


@dataclass(slots=True)
class _MealDemand:
    """Meal-plan draws on one stock_item over the demand window."""
    earliest: date | None = None
    recipe_names: List[str] = field(default_factory=list)
    entry_count: int = 0


@dataclass(slots=True)
class _Ctx:
    today: date
    stock_items_by_id: Dict[UUID, StockItem]
    offer_by_product_id: Dict[UUID, ProductOffer]
    # (stock_item_id → demand). Keys present only when demand exists.
    demand: Dict[UUID, _MealDemand]
    # Cached buy-verdicts by stock_item_id — computed lazily inside the
    # classifier so lines that don't need one don't pay the cost.
    verdicts: Dict[UUID, BuyVerdictDto] = field(default_factory=dict)
    # Cached "days of cover" per stock_item_id. None means "unknown".
    cover_days: Dict[UUID, int | None] = field(default_factory=dict)
    repository: SqlAlchemyRepository | None = None


# ── The handler ───────────────────────────────────────────────────────


class TrimToBudgetHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(
        self,
        shopping_list_id: UUID,
        request: TrimToBudgetRequest,
        user_id: UUID,
    ) -> TrimToBudgetResponse | None:
        user: User | None = self.repository.get(User).by_id(user_id)
        if user is None:
            return None
        shopping_list: ShoppingList | None = (
            self.repository.get(ShoppingList).by_id(shopping_list_id)
        )
        if shopping_list is None:
            return None

        today = household_today(self.repository)
        # Brief §3.3 — a shop scheduled for a later period is measured
        # against *that* period's headroom, not today's.
        headroom_date = shopping_list.planned_shop_date or today
        target = (
            request.budget_target
            if request.budget_target is not None
            else period_headroom(user, headroom_date, self.repository)
        )

        lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
            .eq(shopping_list_id)
        )

        # Bulk-load items + current offers up-front — cheap and lets the
        # classifier stay allocation-free per candidate.
        item_ids = list({l.stock_item_id for l in lines if l.stock_item_id})
        stock_items_by_id: Dict[UUID, StockItem] = {}
        if item_ids:
            loaded = (
                self.repository.get(StockItem)
                .include("stock_level")
                .all(EntityField(StockItem, "id").in_(item_ids))
            )
            stock_items_by_id = {s.id: s for s in loaded}

        product_ids = list({
            l.selected_product_id for l in lines if l.selected_product_id
        })
        offer_by_product_id: Dict[UUID, ProductOffer] = {}
        if product_ids:
            offers = self.repository.get(ProductOffer).all(
                EntityField(ProductOffer, "_product_id").in_(product_ids)
            )
            for offer in offers:
                pid = (
                    getattr(offer, "_product_id", None)
                    or getattr(offer, "product_id", None)
                )
                if pid is not None:
                    offer_by_product_id[pid] = offer

        demand = _load_meal_demand(
            self.repository, today, SHORT_TERM_DEMAND_DAYS,
        )

        ctx = _Ctx(
            today=today,
            stock_items_by_id=stock_items_by_id,
            offer_by_product_id=offer_by_product_id,
            demand=demand,
            repository=self.repository,
        )

        # Projected active-list total from lines that aren't already
        # ticked or deferred.
        projected_total = 0.0
        active_lines: List[ShoppingListLine] = []
        for line in lines:
            if line.is_ticked or line.deferred_by_budget:
                continue
            active_lines.append(line)
            projected_total += _line_projected_total(line, offer_by_product_id)

        # No budget set (target is None) or already under → nothing to do.
        overshoot = 0.0
        if target is not None:
            overshoot = max(0.0, projected_total - target)

        response = TrimToBudgetResponse(
            projected_total=round(projected_total, 2),
            budget_target=round(target, 2) if target is not None else None,
            overshoot=round(overshoot, 2),
            trimmed=[],
            still_over=0.0,
            applied=False,
        )
        if target is None or overshoot <= 0:
            return response

        excluded: Set[UUID] = set(request.exclude_line_ids)
        candidates = _classify_lines(active_lines, ctx, excluded)
        # Cheapest cut first inside a tier isn't what we want — brief §4
        # says highest-priced within a tier for max bang per cut.
        candidates.sort(key=lambda c: (c[0], -c[3]))

        remaining = overshoot
        chosen: List[TrimmedLineDto] = []
        for tier, line, reason_chip, saved in candidates:
            if remaining <= 0:
                break
            chosen.append(TrimmedLineDto(
                line_id=line.id, tier=tier, reason_chip=reason_chip, saved=round(saved, 2),
            ))
            remaining -= saved

        response = TrimToBudgetResponse(
            projected_total=response.projected_total,
            budget_target=response.budget_target,
            overshoot=response.overshoot,
            trimmed=chosen,
            still_over=round(max(0.0, remaining), 2),
            applied=False,
        )

        if request.mode == "apply" and chosen:
            reason_by_id = {t.line_id: t.reason_chip for t in chosen}
            for line in lines:
                reason = reason_by_id.get(line.id)
                if reason is not None:
                    line.deferred_by_budget = True
                    line.deferred_reason = reason
            self.repository.save_changes()
            response = TrimToBudgetResponse(
                projected_total=response.projected_total,
                budget_target=response.budget_target,
                overshoot=response.overshoot,
                trimmed=response.trimmed,
                still_over=response.still_over,
                applied=True,
            )

        return response


# ── Meal-plan demand aggregation ──────────────────────────────────────


def _load_meal_demand(
    repository: SqlAlchemyRepository,
    today: date,
    window_days: int,
) -> Dict[UUID, _MealDemand]:
    """Walk MealPlanEntry × Recipe × RecipeIngredient once and index by
    stock_item_id. Returns per-item earliest scheduled_for, entry count,
    and the referenced recipe names (dedup'd, order-preserving).

    Uses the widest window any tier needs (SHORT_TERM_DEMAND_DAYS =
    7 days). Tier-specific windows (2 / 3 / 7) filter down from this
    inside the classifier."""
    window_end = today + timedelta(days=window_days)
    entries: List[MealPlanEntry] = repository.get(MealPlanEntry).all(
        EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).gte(today)
        & EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).lt(window_end)
        & EntityField(MealPlanEntry, MealPlanEntry.Fields.CONSUMED_AT).is_null()
    )
    if not entries:
        return {}

    # MealPlanEntry.recipe is lazy=noload; use the mapped FK column
    # `_recipe_id` and load recipe rows in one bulk query so we can
    # surface the recipe name in the Tier-5 chip.
    recipe_ids = list({
        rid for rid in (
            getattr(e, "_recipe_id", None) or getattr(e, "recipe_id", None)
            for e in entries
        ) if rid is not None
    })
    if not recipe_ids:
        return {}
    recipes = repository.get(Recipe).all(
        EntityField(Recipe, "id").in_(recipe_ids)
    )
    recipe_name_by_id: Dict[UUID, str] = {r.id: r.name for r in recipes}
    ingredients: List[RecipeIngredient] = repository.get(RecipeIngredient).all(
        EntityField(RecipeIngredient, "_recipe_id").in_(recipe_ids)
    )
    per_recipe: Dict[UUID, List[RecipeIngredient]] = {}
    for ing in ingredients:
        rid = getattr(ing, "_recipe_id", None) or getattr(ing, "recipe_id", None)
        if rid is None or ing.stock_item is None or ing.is_optional:
            continue
        per_recipe.setdefault(rid, []).append(ing)

    result: Dict[UUID, _MealDemand] = {}
    for entry in entries:
        rid = getattr(entry, "_recipe_id", None) or getattr(entry, "recipe_id", None)
        if rid is None:
            continue
        ings = per_recipe.get(rid, [])
        recipe_name = recipe_name_by_id.get(rid)
        for ing in ings:
            item = ing.stock_item
            if item is None:
                continue
            demand = result.get(item.id)
            if demand is None:
                demand = _MealDemand(earliest=entry.scheduled_for)
                result[item.id] = demand
            elif demand.earliest is None or entry.scheduled_for < demand.earliest:
                demand.earliest = entry.scheduled_for
            demand.entry_count += 1
            if recipe_name and recipe_name not in demand.recipe_names:
                demand.recipe_names.append(recipe_name)
    return result


# ── Classification ────────────────────────────────────────────────────


def _line_projected_total(
    line: ShoppingListLine,
    offer_by_product_id: Dict[UUID, ProductOffer],
) -> float:
    """Full-line price (unit × qty) with the same fallback ladder the
    budget projection uses — actual > picked-offer > current-offer."""
    unit = projected_unit_price(line, offer_by_product_id)
    if unit is None:
        return 0.0
    qty = line.quantity or 1
    if qty <= 0:
        return 0.0
    return unit * qty


def _days_of_cover(
    ctx: _Ctx, item: StockItem,
) -> int | None:
    """Estimate remaining days-of-cover from the same 12-month purchase
    history buy-verdict uses. `None` when we don't have enough history
    to make a confident call (< 2 purchases). The classifier translates
    None into the "Not urgent" chip on lines it otherwise wants to cut,
    per brief §5."""
    cached = ctx.cover_days.get(item.id)
    if item.id in ctx.cover_days:
        return cached
    verdict_inputs = _verdict_inputs_for(ctx, item)
    dates = verdict_inputs.unique_purchase_dates
    if len(dates) < 2:
        ctx.cover_days[item.id] = None
        return None
    gaps = [
        (dates[i] - dates[i - 1]).days
        for i in range(1, len(dates))
        if (dates[i] - dates[i - 1]).days > 0
    ]
    if not gaps:
        ctx.cover_days[item.id] = None
        return None
    mean_gap = sum(gaps) / len(gaps)
    days_since_last = (ctx.today - dates[-1]).days
    cover = int(round(mean_gap - days_since_last))
    ctx.cover_days[item.id] = max(0, cover)
    return ctx.cover_days[item.id]


def _verdict_for(ctx: _Ctx, item: StockItem) -> BuyVerdictDto:
    cached = ctx.verdicts.get(item.id)
    if cached is not None:
        return cached
    inputs = _verdict_inputs_for(ctx, item)
    verdict = compose_verdict(inputs)
    ctx.verdicts[item.id] = verdict
    return verdict


def _verdict_inputs_for(ctx: _Ctx, item: StockItem):
    # `_gather_inputs` reads from the repository — safe to call because
    # ctx.repository is set by the handler before classification runs.
    assert ctx.repository is not None
    return _gather_inputs(ctx.repository, item)


def _stock_band(item: StockItem | None) -> str:
    if item is None or item.stock_level is None:
        return "unknown"
    if is_out_of_stock(item.stock_level):
        return "out"
    if is_low_stock(item.stock_level):
        return "low"
    return "stocked"


def _has_demand_within(demand: _MealDemand | None, today: date, days: int) -> bool:
    if demand is None or demand.earliest is None:
        return False
    return (demand.earliest - today).days < days


def _classify_lines(
    lines: List[ShoppingListLine],
    ctx: _Ctx,
    excluded: Set[UUID],
) -> List[tuple[int, ShoppingListLine, str, float]]:
    """Return (tier_index, line, reason_chip, saved_amount) for every
    line eligible to cut. Tier index is 1..5 (lower = safer)."""
    out: List[tuple[int, ShoppingListLine, str, float]] = []
    for line in lines:
        if line.id in excluded:
            continue
        if not line.stock_item_id:
            # Product-only lines don't have a stock_item to reason about;
            # skip. (Rare — usually cart-adds from the products surface.)
            continue
        item = ctx.stock_items_by_id.get(line.stock_item_id)
        if item is None:
            continue

        saved = _line_projected_total(line, ctx.offer_by_product_id)
        if saved < MIN_LINE_VALUE:
            # Brief §4 never-cut: sub-$2 lines aren't worth the chip.
            continue

        # ── Never-cut set ─────────────────────────────────────────────
        # Essentials.
        if getattr(item, "is_flagged", False):
            continue
        # Meals booked in next 2 days.
        demand = ctx.demand.get(item.id)
        if _has_demand_within(demand, ctx.today, NEAR_TERM_DEMAND_DAYS):
            continue
        # verdict=buy on low/out.
        band = _stock_band(item)
        verdict = _verdict_for(ctx, item)
        if verdict.verdict == "buy" and band in {"low", "out"}:
            continue

        # ── Tier 1 — habit items with no short-term demand, not out ──
        short_term_demand = _has_demand_within(
            demand, ctx.today, SHORT_TERM_DEMAND_DAYS,
        )
        if (
            line.added_via == ADDED_VIA_AUTO_FREQUENTLY_ADDED
            and not short_term_demand
            and band != "out"
        ):
            out.append((1, line, REASON_HABIT_CAN_WAIT, saved))
            continue

        # ── Tier 2 — low-stock with cover, no short-term demand ──────
        if (
            line.added_via == ADDED_VIA_AUTO_LOW_STOCK
            and not short_term_demand
        ):
            cover = _days_of_cover(ctx, item)
            if cover is None:
                out.append((2, line, REASON_NOT_URGENT, saved))
                continue
            if cover >= TIER_2_MIN_COVER_DAYS:
                out.append((
                    2, line,
                    REASON_COVER_LEFT.format(n=cover),
                    saved,
                ))
                continue

        # ── Tier 3 — verdict=wait, no demand in 3 days, not out ──────
        if (
            verdict.verdict == "wait"
            and not _has_demand_within(demand, ctx.today, BUY_VERDICT_DEMAND_DAYS)
            and band != "out"
        ):
            out.append((3, line, REASON_ABOVE_USUAL_PRICE, saved))
            continue

        # ── Tier 4 — out, no meal booked in 7 days ────────────────────
        if band == "out" and not short_term_demand:
            out.append((4, line, REASON_OUT_NO_MEAL, saved))
            continue

        # ── Tier 5 — recipe/meal-plan items scheduled ≥ 5 days out ────
        if (
            line.added_via in (ADDED_VIA_AUTO_RECIPE, ADDED_VIA_AUTO_MEAL_PLAN)
            and demand is not None
            and demand.earliest is not None
            and (demand.earliest - ctx.today).days >= FAR_OUT_MIN_DAYS
        ):
            if demand.entry_count <= 1 and demand.recipe_names:
                recipe = demand.recipe_names[0]
                day = demand.earliest.strftime("%a")
                out.append((
                    5, line,
                    REASON_FOR_RECIPE_ON_DAY.format(recipe=recipe, day=day),
                    saved,
                ))
            else:
                out.append((
                    5, line,
                    REASON_NEEDED_FOR_N_MEALS.format(n=demand.entry_count),
                    saved,
                ))
    return out


# ── Route ─────────────────────────────────────────────────────────────


def _current_user_id() -> UUID | None:
    raw = session.get(SESSION_USER_ID_KEY)
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        return None


def _response_payload(response: TrimToBudgetResponse) -> dict:
    return {
        "projected_total": response.projected_total,
        "budget_target": response.budget_target,
        "overshoot": response.overshoot,
        "trimmed": [
            {
                "line_id": str(t.line_id),
                "tier": t.tier,
                "reason_chip": t.reason_chip,
                "saved": t.saved,
            }
            for t in response.trimmed
        ],
        "still_over": response.still_over,
        "applied": response.applied,
    }


@SHOPPING_LIST_ROUTER.route(
    "/<uuid:shopping_list_id>/trim-to-budget", methods=["POST"],
)
@has_request_body(TrimToBudgetRequest)
def trim_to_budget(shopping_list_id: UUID):
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized()
    request: TrimToBudgetRequest = get_request_body()
    if request.mode not in {"preview", "apply"}:
        # Pydantic could enforce this via Literal[...], but the surface
        # is small enough that a runtime check keeps the error message
        # clearer than a validator dump.
        return {"error": "mode must be 'preview' or 'apply'"}, 400
    response = TrimToBudgetHandler(SqlAlchemyRepository()).handle(
        shopping_list_id, request, user_id,
    )
    if response is None:
        return not_found("ShoppingList", shopping_list_id)
    _LOGGER.info(
        "trim-to-budget list=%s mode=%s overshoot=%.2f cuts=%d still_over=%.2f",
        shopping_list_id, request.mode, response.overshoot,
        len(response.trimmed), response.still_over,
    )
    return ok(_response_payload(response))
