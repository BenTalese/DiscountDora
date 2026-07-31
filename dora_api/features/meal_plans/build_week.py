"""FU-596 — "Build my week" auto-planner (server-owned meal selection + placement).

The old "Plan step-by-step" builder was just the planner's recipe picker in a
modal — the user hand-picked every meal and the client spread them across days
(dropping every one into the first slot, hence FU-596). This replaces it with a
genuine *generator*: given light guidance (emphasis, meal count, slots, scope,
optional budget cap) Dora proposes a week — the client renders it as an editable
preview and commits through the existing create/update path.

  POST /api/meal-plans/auto-build  — preview only; never persists.

**R-003 / state-ownership:** recipe *selection* and slot/day *placement* are
cross-entity domain rules, so they live here, not in the SPA — mirroring the
`swap_suggestions.py` shape: a **pure ranker** (`select_recipes` / `place_entries`,
driven by fixtures in the unit tests) + a thin repo-touching orchestrator
(`compute_auto_build`).

**Not a Decision-7 regression:** PROPOSAL_MEAL_PLANS §3.6 cut the *"Suggest meals
I can cook now"* browse surface (that belongs on Cookbook). This is a plan
generator; it only *uses* the cookable / expiring signals to rank, it does not
resurrect a cookable-now list page.
"""
import logging
import random
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.user import User
from dora_api.features.app_settings.clock import household_today
from dora_api.features.auth.register_user import SESSION_USER_ID_KEY
from dora_api.features.budget.budget import period_bounds, period_spent
from dora_api.features.meal_slots.manage_meal_slots import GetMealSlotsHandler
from dora_api.features.recipes.get_recipes import (
    GetRecipesHandler, count_expiring_ingredients_per_recipe)
from dora_api.features.recipes.recipe_cost import estimate_costs_for
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.query_options import QueryOptions
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

from flask import session

_LOGGER = logging.getLogger(__name__)

WEEK_LENGTH_DAYS = 7
# "expiring soon" horizon for the use-up-stock emphasis — matches the cookbook
# "Uses expiring ingredients" filter (get_recipes / rescue feed, R-003).
EXPIRING_HORIZON_DAYS = 14
# Hard ceiling so a bad client can't ask us to place 500 meals.
MAX_MEALS = 21

# ── Emphasis + reason-chip vocabulary (frozen server-side, R-003) ──────────

EMPHASIS_USE_UP_STOCK = "use_up_stock"
EMPHASIS_VARIETY = "variety"
EMPHASIS_FAVOURITES = "favourites"
EMPHASIS_SURPRISE = "surprise"
_EMPHASES = frozenset({
    EMPHASIS_USE_UP_STOCK, EMPHASIS_VARIETY, EMPHASIS_FAVOURITES, EMPHASIS_SURPRISE,
})

CHIP_USES_EXPIRING = "uses_expiring"        # "Uses stock that's expiring"
CHIP_COOKABLE_NOW = "cookable_now"          # "You have everything for this"
CHIP_FAVOURITE = "favourite"                # "A favourite"
CHIP_NOT_MADE_RECENTLY = "not_made_recently"  # "Haven't had in a while"
CHIP_VARIETY = "variety"                    # "Adds variety"
CHIP_BUDGET = "budget_friendly"             # "Cheaper — keeps you on budget"
CHIP_PICKED = "picked"                      # neutral fallback


@dataclass(frozen=True, slots=True)
class RecipeCandidate:
    """The slim view the pure ranker needs — deliberately decoupled from
    `RecipeDto` so the ranker's unit tests can drive it with plain fixtures."""
    recipe_id: UUID
    name: str
    time_of_day: Optional[str]
    cookable: Optional[bool]
    expiring_count: int
    is_favourite: bool
    plan_count: int
    not_made_recently: bool
    cuisine_id: Optional[UUID]
    category_id: Optional[UUID]
    estimated_cost: Optional[float]
    servings: Optional[int]
    missing_stock_item_names: tuple


@dataclass(frozen=True, slots=True)
class ProposedEntry:
    recipe_id: UUID
    recipe_name: str
    scheduled_for: date
    slot: str
    servings: int
    reason_chip: str
    cookable: Optional[bool]
    missing_stock_item_names: List[str]
    estimated_cost: Optional[float]


@dataclass(frozen=True, slots=True)
class AutoBuildResponse:
    scope: str
    entries: List[ProposedEntry]
    slots_used: List[str]
    cost_total: Optional[float]
    budget_amount: Optional[float]
    projected_over: bool


# ── Pure ranker (no repo — driven by fixtures in the unit tests) ───────────


def _base_score(c: RecipeCandidate, emphasis: str, rng: Optional[random.Random]) -> float:
    """How strongly this recipe fits the chosen emphasis (higher = better).
    Variety spread is applied on top of this during selection, not here."""
    if emphasis == EMPHASIS_USE_UP_STOCK:
        return (
            3.0 * c.expiring_count
            + (2.0 if c.cookable is True else 0.0)
            + (0.5 if c.not_made_recently else 0.0)
        )
    if emphasis == EMPHASIS_FAVOURITES:
        return (
            (3.0 if c.is_favourite else 0.0)
            + 0.2 * c.plan_count
            + (0.5 if c.not_made_recently else 0.0)
        )
    if emphasis == EMPHASIS_VARIETY:
        return (1.0 if c.not_made_recently else 0.0) + (0.3 if c.is_favourite else 0.0)
    if emphasis == EMPHASIS_SURPRISE:
        # Mostly random, with a gentle lean toward recipes not made recently.
        jitter = rng.random() if rng is not None else 0.0
        return jitter + (0.5 if c.not_made_recently else 0.0)
    return 0.0


def _variety_weight(emphasis: str) -> float:
    """How hard to penalise repeating a cuisine/category already picked. Strong
    for the Variety emphasis; a mild anti-repeat nudge for everything else."""
    return 2.0 if emphasis == EMPHASIS_VARIETY else 0.5


def select_recipes(
    candidates: List[RecipeCandidate],
    emphasis: str,
    count: int,
    exclude_ids: set,
    rng: Optional[random.Random] = None,
) -> List[RecipeCandidate]:
    """Greedily pick `count` **distinct** recipes best matching `emphasis`,
    excluding `exclude_ids` (already on the plan), spreading cuisine/category so
    the week isn't four pastas. Deterministic for a given input + rng."""
    # Stable ordering so ties resolve predictably (and tests are deterministic).
    eligible = sorted(
        (c for c in candidates if c.recipe_id not in exclude_ids),
        key=lambda c: (c.name.lower(), str(c.recipe_id)),
    )
    selected: List[RecipeCandidate] = []
    used_cuisine: Counter = Counter()
    used_category: Counter = Counter()
    vweight = _variety_weight(emphasis)

    while len(selected) < count and eligible:
        best = None
        best_score = None
        for c in eligible:
            repeats = used_cuisine[c.cuisine_id] + used_category[c.category_id]
            score = _base_score(c, emphasis, rng) - vweight * repeats
            if best_score is None or score > best_score:
                best, best_score = c, score
        assert best is not None
        selected.append(best)
        eligible.remove(best)
        used_cuisine[best.cuisine_id] += 1
        used_category[best.category_id] += 1
    return selected


def apply_budget_cap(
    selected: List[RecipeCandidate],
    pool: List[RecipeCandidate],
    budget_remaining: float,
) -> tuple[List[RecipeCandidate], set]:
    """Best-effort: while the selection's priced cost exceeds what's left of the
    budget, swap the dearest picked recipe for the cheapest cheaper alternative
    from `pool`. Returns the (possibly changed) list + the set of swapped-in ids
    (for the budget reason chip). Never guarantees under-budget — same honest
    posture as the FU-451 swap ranker."""

    def cost(c: RecipeCandidate) -> Optional[float]:
        return c.estimated_cost

    def total(items: List[RecipeCandidate]) -> float:
        return sum((cost(x) or 0.0) for x in items)

    swapped: set = set()
    # Cheapest-first pool of priced alternatives not already selected.
    cheap_pool = sorted(
        (c for c in pool if cost(c) is not None),
        key=lambda c: cost(c),  # type: ignore[arg-type]
    )
    guard = 0
    while total(selected) > budget_remaining and guard < len(selected):
        guard += 1
        priced = [c for c in selected if cost(c) is not None]
        if not priced:
            break
        dearest = max(priced, key=lambda c: cost(c))  # type: ignore[arg-type]
        selected_ids = {s.recipe_id for s in selected}
        replacement = next(
            (c for c in cheap_pool
             if c.recipe_id not in selected_ids and cost(c) < cost(dearest)),  # type: ignore[operator]
            None,
        )
        if replacement is None:
            break
        selected[selected.index(dearest)] = replacement
        cheap_pool.remove(replacement)
        swapped.add(replacement.recipe_id)
    return selected, swapped


def _pick_slot(
    c: RecipeCandidate, slots: List[str], day_load: dict, slot_sequence: dict,
) -> str:
    """Smart slot placement (FU-596 fix): honour the recipe's own `time_of_day`
    when it's one of the allowed slots; otherwise fall to the least-loaded slot
    for the day (tie-broken by the household slot order, then name)."""
    if c.time_of_day and c.time_of_day in slots:
        return c.time_of_day
    return min(slots, key=lambda s: (day_load.get(s, 0), slot_sequence.get(s, 0), s))


def place_entries(
    selected: List[RecipeCandidate],
    days: List[date],
    allowed_slots: List[str],
    slot_sequence: dict,
) -> List[tuple]:
    """Spread the picks day-major across `days`, wrapping to a second per day
    once each has one. Returns `(candidate, day, slot)` triples."""
    if not days:
        return []
    slots = allowed_slots or ["Dinner"]
    load = {d: {s: 0 for s in slots} for d in days}
    placements: List[tuple] = []
    for i, c in enumerate(selected):
        day = days[i % len(days)]
        slot = _pick_slot(c, slots, load[day], slot_sequence)
        load[day][slot] += 1
        placements.append((c, day, slot))
    return placements


def reason_chip(c: RecipeCandidate, emphasis: str, budget_swapped: bool) -> str:
    if budget_swapped:
        return CHIP_BUDGET
    if c.expiring_count > 0:
        return CHIP_USES_EXPIRING
    if emphasis == EMPHASIS_USE_UP_STOCK and c.cookable is True:
        return CHIP_COOKABLE_NOW
    if emphasis == EMPHASIS_FAVOURITES and c.is_favourite:
        return CHIP_FAVOURITE
    if c.not_made_recently:
        return CHIP_NOT_MADE_RECENTLY
    if c.is_favourite:
        return CHIP_FAVOURITE
    return CHIP_VARIETY if emphasis == EMPHASIS_VARIETY else CHIP_PICKED


# ── Request / repo-touching orchestration ──────────────────────────────────


class AutoBuildRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # "week" fills the upcoming days of the week beginning `start_date` (a
    # Monday); "day" fills just `start_date` (the "plan Wednesday, shop, cook"
    # use case).
    scope: str = "week"
    start_date: date
    meal_count: int = Field(default=7, ge=1, le=MAX_MEALS)
    emphasis: str = EMPHASIS_USE_UP_STOCK
    # Empty ⇒ spread across every household slot. One name ⇒ single-slot
    # (e.g. Dinner only). A subset ⇒ spread across just those.
    slot_names: List[str] = Field(default_factory=list)
    budget_cap: bool = False


def _current_user_id() -> Optional[UUID]:
    raw = session.get(SESSION_USER_ID_KEY)
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        return None


def _budget_remaining(repository: SqlAlchemyRepository, user: Optional[User]) -> Optional[float]:
    """What's left of this period's grocery budget, or None when money features
    are off / no budget is set (so the budget cap is a no-op). Mirrors the money
    gate + period math in `swap_suggestions.compute_suggestions` (R-003 —
    same budget engine, `budget.period_bounds` / `period_spent`)."""
    if user is None or not user.money_features_enabled:
        return None
    settings = repository.get(AppSetting).all()
    if not settings or not settings[0].money_enabled:
        return None
    if user.budget_amount is None:
        return None
    today = household_today(repository)
    p_start, p_end = period_bounds(today, user.budget_period)
    spent = period_spent(user, p_start, p_end, repository)
    return float(user.budget_amount) - spent


def _scope_days(scope: str, start: date, today: date) -> List[date]:
    """Upcoming days the build may place into. Past days are dropped so we never
    schedule into yesterday (create_meal_plan rejects past entries anyway)."""
    if scope == "day":
        return [start] if start >= today else []
    week = [start + timedelta(days=i) for i in range(WEEK_LENGTH_DAYS)]
    return [d for d in week if d >= today]


def _resolve_allowed_slots(requested: List[str], household_slots: List[str]) -> List[str]:
    """The pool of slots to place into: the requested subset (intersected with
    the live vocabulary, preserving household order) or all household slots."""
    if requested:
        wanted = set(requested)
        pool = [s for s in household_slots if s in wanted]
        if pool:
            return pool
    return list(household_slots)


def _planned_recipe_ids_in_range(repository, days: List[date]) -> set:
    """Recipe ids already scheduled (unconsumed) within the build's day range —
    excluded so a build never re-suggests a meal you've already planned there."""
    if not days:
        return set()
    lo, hi = min(days), max(days)
    entries = (
        repository.get(MealPlanEntry)
        .include(MealPlanEntry.Fields.RECIPE)
        .all(
            EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).gte(lo)
            & EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).lte(hi)
            & EntityField(MealPlanEntry, MealPlanEntry.Fields.CONSUMED_AT).is_null()
        )
    )
    return {e.recipe.id for e in entries if e.recipe}


def _all_recipe_dtos(repository: SqlAlchemyRepository) -> list:
    # Bounded household cookbook — one large page (mirrors swap_suggestions).
    return list(
        GetRecipesHandler(repository)
        .handle(QueryOptions(page=1, limit=10_000))
        .items
    )


def compute_auto_build(
    repository: SqlAlchemyRepository,
    request: AutoBuildRequest,
    user: Optional[User],
    rng: Optional[random.Random] = None,
) -> AutoBuildResponse:
    today = household_today(repository)
    days = _scope_days(request.scope, request.start_date, today)

    slot_dtos = GetMealSlotsHandler(repository).handle()
    household_slots = [s.name for s in slot_dtos]
    slot_sequence = {s.name: s.sequence for s in slot_dtos}
    allowed_slots = _resolve_allowed_slots(request.slot_names, household_slots)

    recipes = _all_recipe_dtos(repository)
    _, expiring_counts = count_expiring_ingredients_per_recipe(
        repository, EXPIRING_HORIZON_DAYS,
    )
    cost_est = estimate_costs_for(repository, recipes)

    candidates = [
        RecipeCandidate(
            recipe_id=r.recipe_id,
            name=r.name,
            time_of_day=r.time_of_day,
            cookable=r.cookable,
            expiring_count=expiring_counts.get(r.recipe_id, 0),
            is_favourite=r.is_favourite,
            plan_count=r.plan_count,
            not_made_recently=r.not_made_recently,
            cuisine_id=r.cuisine_id,
            category_id=r.category_id,
            estimated_cost=cost_est[r.recipe_id].estimated_cost,
            servings=r.servings,
            missing_stock_item_names=tuple(r.missing_stock_item_names),
        )
        for r in recipes
    ]

    excluded = _planned_recipe_ids_in_range(repository, days)
    emphasis = request.emphasis if request.emphasis in _EMPHASES else EMPHASIS_USE_UP_STOCK
    # Never place two meals in the same day+slot: cap the count at the grid size.
    grid = len(days) * max(len(allowed_slots), 1)
    count = max(1, min(request.meal_count, grid)) if days else 0

    selected = select_recipes(candidates, emphasis, count, excluded, rng)

    swapped: set = set()
    budget_remaining = _budget_remaining(repository, user)
    if request.budget_cap and budget_remaining is not None:
        selected_ids = {c.recipe_id for c in selected}
        pool = [c for c in candidates if c.recipe_id not in selected_ids and c.recipe_id not in excluded]
        selected, swapped = apply_budget_cap(selected, pool, budget_remaining)

    placements = place_entries(selected, days, allowed_slots, slot_sequence)
    entries = [
        ProposedEntry(
            recipe_id=c.recipe_id,
            recipe_name=c.name,
            scheduled_for=day,
            slot=slot,
            servings=1,
            reason_chip=reason_chip(c, emphasis, c.recipe_id in swapped),
            cookable=c.cookable,
            missing_stock_item_names=list(c.missing_stock_item_names),
            estimated_cost=c.estimated_cost,
        )
        for (c, day, slot) in placements
    ]

    priced = [e.estimated_cost for e in entries if e.estimated_cost is not None]
    cost_total = round(sum(priced), 2) if priced else None
    projected_over = (
        budget_remaining is not None
        and cost_total is not None
        and cost_total > budget_remaining
    )

    return AutoBuildResponse(
        scope=request.scope,
        entries=entries,
        slots_used=allowed_slots,
        cost_total=cost_total,
        budget_amount=float(user.budget_amount) if (user and user.budget_amount is not None) else None,
        projected_over=projected_over,
    )


def _entry_payload(e: ProposedEntry) -> dict:
    return {
        "recipe_id": str(e.recipe_id),
        "recipe_name": e.recipe_name,
        "scheduled_for": e.scheduled_for.isoformat(),
        "slot": e.slot,
        "servings": e.servings,
        "reason_chip": e.reason_chip,
        "cookable": e.cookable,
        "missing_stock_item_names": e.missing_stock_item_names,
        "estimated_cost": e.estimated_cost,
    }


def _response_payload(r: AutoBuildResponse) -> dict:
    return {
        "scope": r.scope,
        "entries": [_entry_payload(e) for e in r.entries],
        "slots_used": r.slots_used,
        "cost_total": r.cost_total,
        "budget_amount": r.budget_amount,
        "projected_over": r.projected_over,
    }


@MEAL_PLAN_ROUTER.route("/auto-build", methods=["POST"])
@has_request_body(AutoBuildRequest)
def auto_build():
    request: AutoBuildRequest = get_request_body()
    if request.scope not in ("week", "day"):
        return bad_request("scope must be 'week' or 'day'.")

    repo = SqlAlchemyRepository()
    user_id = _current_user_id()
    user = repo.get(User).by_id(user_id) if user_id else None

    today = household_today(repo)
    if request.scope == "day" and request.start_date < today:
        return bad_request("Can't build a plan for a day in the past.")

    result = compute_auto_build(repo, request, user, rng=random.Random())
    _LOGGER.info(
        "Auto-build (%s, emphasis=%s, budget_cap=%s) proposed %d meal(s).",
        request.scope, request.emphasis, request.budget_cap, len(result.entries),
    )
    return ok(_response_payload(result))
