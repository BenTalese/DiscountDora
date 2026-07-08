"""P2-04 — deterministic suggestion generators.

Each generator returns a list of `Suggestion` dicts derived from current
app state. The endpoint in `suggestions.py` runs every generator, then
filters the combined output against the user's suppression list (dismiss
/ snooze decisions) before returning.

We *don't* let the LLM generate facts here — that's the cross-cutting
rule from PROMPT_PLAN_PART_2. The model only summarises if the SPA
chooses to render `reason` through it; the underlying claim ("you're
8 days past your usual cadence for milk") is computed by Python.

Each generator owns its `kind` and its `dedup_key` policy:
  - "use_soon"        — dedup by stock_item_id (one suggestion per item)
  - "over_budget"     — dedup by ISO period_start (one per period)
  - "likely_due"      — dedup by stock_item_id
  - "frequent_waster" — dedup by stock_item_name
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.recipe_ingredient import RecipeIngredient
from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.entities.user import User
from dora_api.features.app_settings.clock import household_today
from dora_api.features.shopping_lists._line_price import line_paid_unit_price
from dora_api.features.stock_items.pantry_belief import gather_beliefs_for_items
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Severity drives sort order + the SPA's chip colour. "high" = act
# today, "medium" = within the week, "low" = soft nudge.
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

# Generator kinds. Used as `Suggestion.kind` + the suppression `kind`
# column. Keep these stable — changing one orphans existing
# suppressions, which is the opposite of the user's intent.
KIND_USE_SOON = "use_soon"
KIND_OVER_BUDGET = "over_budget"
KIND_LIKELY_DUE = "likely_due"
KIND_FREQUENT_WASTER = "frequent_waster"
KIND_PANTRY_CHECK = "pantry_check"


@dataclass(frozen=True, slots=True)
class Suggestion:
    kind: str
    dedup_key: str
    severity: str
    title: str
    body: str
    # Plain-English why-line. Rendered as the "Why?" expander in the SPA;
    # also handed to the assistant tool so Dora can repeat the reason
    # back if asked.
    reason: str
    # An optional primary CTA. `path` is the SPA route to drop the user
    # at; `label` is the button text. The caller is the final authority
    # on what "accept" means — we deliberately don't auto-mutate.
    primary_action: dict[str, str] | None = None
    # Free-form payload the model can reference (e.g. the stock item
    # name for follow-up "tell me about milk" calls). Kept small.
    payload: dict[str, Any] = field(default_factory=dict)


# ── 1. Use soon ─────────────────────────────────────────────────────────
# At-risk items within 3 days. Tighter than the rescue feed's default 7
# because the suggestion inbox should only nag about *imminent* stuff.

_USE_SOON_HORIZON_DAYS = 3


def generate_use_soon(repository: SqlAlchemyRepository) -> list[Suggestion]:
    # R-021 — household-tz "today" for the use-soon horizon.
    today = household_today(repository)
    cutoff = today + timedelta(days=_USE_SOON_HORIZON_DAYS)
    items: list[StockItem] = repository.get(StockItem).all(
        EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).is_not_null()
        & EntityField(StockItem, StockItem.Fields.EXPIRY_DATE).lte(cutoff)
    )
    out: list[Suggestion] = []
    for item in items:
        if not item.expiry_date:
            continue
        days = (item.expiry_date - today).days
        if days < 0:
            severity = SEVERITY_HIGH
            window = f"expired {abs(days)} day{'s' if abs(days) != 1 else ''} ago"
        elif days == 0:
            severity = SEVERITY_HIGH
            window = "today"
        elif days == 1:
            severity = SEVERITY_HIGH
            window = "tomorrow"
        else:
            severity = SEVERITY_MEDIUM
            window = f"in {days} days"
        out.append(Suggestion(
            kind=KIND_USE_SOON,
            dedup_key=str(item.id),
            severity=severity,
            title=f"Use {item.name} soon",
            body=f"{item.name} expires {window}.",
            reason=(
                f"Its recorded expiry date is {item.expiry_date.isoformat()}, "
                f"which is within the 3-day rescue horizon."
            ),
            primary_action={
                "path": f"/stock/{item.id}",
                "label": "Open item",
            },
            payload={"stock_item_id": str(item.id), "item_name": item.name},
        ))
    return out


# ── 2. Over budget ──────────────────────────────────────────────────────
# Single-user query — uses the existing budget handler so the period
# math stays in one place.

def generate_over_budget(repository: SqlAlchemyRepository, user_id: UUID | None) -> list[Suggestion]:
    if user_id is None:
        return []
    # Inline import — avoids a circular dependency between
    # features/suggestions and features/budget.
    from dora_api.features.budget.budget import GetBudgetStatusHandler

    dto = GetBudgetStatusHandler(SqlAlchemyRepository()).handle(user_id)
    if dto is None or not dto.enabled or not dto.over_budget or dto.amount is None:
        return []
    over_by = dto.spent - dto.amount
    return [Suggestion(
        kind=KIND_OVER_BUDGET,
        dedup_key=dto.period_start or "current",
        severity=SEVERITY_HIGH,
        title="You're over budget this " + dto.period.replace("ly", ""),
        body=(
            f"Spent ${dto.spent:.2f} of your ${dto.amount:.2f} target — "
            f"${over_by:.2f} over."
        ),
        reason=(
            f"Spend across archived shopping lists with completed_at in "
            f"[{dto.period_start}, {dto.period_end}) totals ${dto.spent:.2f}, "
            f"which exceeds your configured budget of ${dto.amount:.2f}."
        ),
        primary_action={"path": "/settings/preferences", "label": "Review budget"},
        payload={"amount": dto.amount, "spent": dto.spent, "over_by": round(over_by, 2)},
    )]


# ── 3. Likely due (cadence) ─────────────────────────────────────────────
# Walks archived shopping-list lines per stock item and infers a buy
# cadence (mean gap between unique completion dates). If `today` is past
# `last_paid_at + cadence`, flag the item.

_LIKELY_DUE_MIN_SAMPLES = 3       # Anything less is too noisy.
_LIKELY_DUE_MAX_GAP_DAYS = 90     # >90 days is "occasional" — don't pester.


def generate_likely_due(repository: SqlAlchemyRepository) -> list[Suggestion]:
    archived = repository.get(ShoppingList).all(
        EntityField(ShoppingList, ShoppingList.Fields.STATUS).eq(SHOPPING_LIST_STATUS_DONE)
    )
    archived_lookup: dict[UUID, ShoppingList] = {l.id: l for l in archived}
    if not archived_lookup:
        return []

    lines: list[ShoppingListLine] = repository.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
        .in_(list(archived_lookup.keys()))
    )
    # Bucket completion dates per stock item.
    by_item: dict[UUID, list[date]] = {}
    for line in lines:
        if line_paid_unit_price(line) is None:
            # Without a price the line might not represent a real
            # purchase (e.g. never-ticked). Use price-presence as the
            # "this was actually bought" signal — matches the
            # purchase_price_stats heuristic (same actual→picked ladder).
            continue
        lst = archived_lookup.get(line.shopping_list_id)
        if lst is None or lst.completed_at is None:
            continue
        by_item.setdefault(line.stock_item_id, []).append(lst.completed_at.date())

    # Pre-fetch names so we don't N+1.
    item_ids = list(by_item.keys())
    items_by_id: dict[UUID, StockItem] = {}
    if item_ids:
        for it in repository.get(StockItem).all(EntityField(StockItem, "id").in_(item_ids)):
            items_by_id[it.id] = it

    # R-021 — anchor "due today" against household-tz today.
    today = household_today(repository)
    out: list[Suggestion] = []
    for item_id, dates in by_item.items():
        unique_sorted = sorted(set(dates))
        if len(unique_sorted) < _LIKELY_DUE_MIN_SAMPLES:
            continue
        gaps = [
            (unique_sorted[i] - unique_sorted[i - 1]).days
            for i in range(1, len(unique_sorted))
            if (unique_sorted[i] - unique_sorted[i - 1]).days > 0
        ]
        if not gaps:
            continue
        avg_gap = sum(gaps) / len(gaps)
        if avg_gap > _LIKELY_DUE_MAX_GAP_DAYS:
            continue
        last = unique_sorted[-1]
        days_since = (today - last).days
        if days_since < avg_gap:
            continue
        overdue_by = days_since - avg_gap
        item = items_by_id.get(item_id)
        if item is None:
            continue
        out.append(Suggestion(
            kind=KIND_LIKELY_DUE,
            dedup_key=str(item_id),
            severity=SEVERITY_LOW if overdue_by < avg_gap else SEVERITY_MEDIUM,
            title=f"You're probably due for {item.name}",
            body=(
                f"You usually buy {item.name} every "
                f"~{round(avg_gap)} day{'s' if round(avg_gap) != 1 else ''}; "
                f"last picked up {days_since} days ago."
            ),
            reason=(
                f"Across {len(unique_sorted)} archived shops, the mean gap "
                f"between purchases of {item.name} is {avg_gap:.1f} days. "
                f"Last purchased on {last.isoformat()}."
            ),
            primary_action={"path": "/shopping-lists", "label": "Open shopping lists"},
            payload={"stock_item_id": str(item_id), "item_name": item.name},
        ))
    return out


# ── 4. Frequent waster ──────────────────────────────────────────────────
# 3+ waste events for the same item in the last 90 days. Suggests
# "buy smaller next time"; the existing waste-events table is the source.

_FREQUENT_WASTER_WINDOW_DAYS = 90
_FREQUENT_WASTER_MIN_EVENTS = 3


def generate_frequent_waster(repository: SqlAlchemyRepository) -> list[Suggestion]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=_FREQUENT_WASTER_WINDOW_DAYS)
    events: list[StockItemWasteEvent] = repository.get(StockItemWasteEvent).all(
        EntityField(StockItemWasteEvent, StockItemWasteEvent.Fields.OCCURRED_AT).gte(cutoff)
    )
    if not events:
        return []
    # Bucket on (stock_item_id, name) so a rename doesn't split history and
    # so a deleted item (FK set null) still appears under its captured name.
    # We need the id to deep-link the suggestion at an actual page; events
    # whose item was deleted (id is None) can't deep-link and are skipped.
    counter: dict[tuple, dict] = {}
    for event in events:
        key = (event.stock_item_id, event.stock_item_name)
        bucket = counter.setdefault(key, {
            "count": 0,
            "stock_item_id": event.stock_item_id,
            "name": event.stock_item_name,
        })
        bucket["count"] += 1

    out: list[Suggestion] = []
    for bucket in counter.values():
        if bucket["count"] < _FREQUENT_WASTER_MIN_EVENTS:
            continue
        stock_item_id = bucket["stock_item_id"]
        if stock_item_id is None:
            continue
        name = bucket["name"]
        out.append(Suggestion(
            kind=KIND_FREQUENT_WASTER,
            dedup_key=str(stock_item_id),
            severity=SEVERITY_LOW,
            title=f"Buy less {name}?",
            body=(
                f"You've logged {bucket['count']} waste events for {name} "
                f"in the last {_FREQUENT_WASTER_WINDOW_DAYS} days."
            ),
            reason=(
                f"Over the last {_FREQUENT_WASTER_WINDOW_DAYS} days, {name} "
                f"has shown up in {bucket['count']} waste events. A smaller "
                f"pack size or longer gaps between buys may help."
            ),
            primary_action={
                "path": f"/stock/{stock_item_id}",
                "label": "Open item",
            },
            payload={
                "stock_item_id": str(stock_item_id),
                "item_name": name,
                "events": bucket["count"],
            },
        ))
    return out


# ── 5. Pantry quick-check (P8-07 "ask only when it matters") ────────────
# The Zero-Input Pantry never bulk-prompts a stocktake. It asks a SINGLE
# targeted quick-check only when a *decision* hinges on an item whose
# inferred level we're genuinely unsure about — you're drafting a shop
# (buy decision) or a planned meal needs it (cook decision), and the belief
# confidence is low. Gated on the per-user `inferred_pantry_enabled` opt-out.

_PANTRY_CHECK_HORIZON_DAYS = 7   # planned meals within a week are "imminent"
_PANTRY_CHECK_MAX = 3            # never a bulk prompt — a few at most


def generate_pantry_check(
    repository: SqlAlchemyRepository, user_id: UUID | None
) -> list[Suggestion]:
    if user_id is None:
        return []
    user: User | None = repository.get(User).by_id(user_id)
    if user is None or not user.inferred_pantry_enabled:
        return []

    today = household_today(repository)

    # ── Which items does a pending decision hinge on? ──
    # (a) On an open (non-archived) shopping list → a buy decision.
    open_lists = repository.get(ShoppingList).all(
        EntityField(ShoppingList, ShoppingList.Fields.STATUS).ne(SHOPPING_LIST_STATUS_DONE)
    )
    in_play: set[UUID] = set()
    decision_by_item: dict[UUID, str] = {}
    if open_lists:
        open_lines = repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, ShoppingListLine.Fields.SHOPPING_LIST_ID)
            .in_([l.id for l in open_lists])
        )
        for line in open_lines:
            if line.stock_item_id is not None:
                in_play.add(line.stock_item_id)
                decision_by_item.setdefault(line.stock_item_id, "it's on a shopping list you're building")

    # (b) In a meal planned within the next week → a cook decision. Read the
    #     entry's `_recipe_id` FK directly to avoid lazy-loading each recipe.
    horizon = today + timedelta(days=_PANTRY_CHECK_HORIZON_DAYS)
    entries = repository.get(MealPlanEntry).all(
        EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).gte(today)
        & EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR).lte(horizon)
    )
    recipe_ids = {e._recipe_id for e in entries if getattr(e, "_recipe_id", None)}  # noqa: SLF001
    if recipe_ids:
        ingredients = repository.get(RecipeIngredient).all(
            EntityField(RecipeIngredient, "_recipe_id").in_(list(recipe_ids))
        )
        for ing in ingredients:
            sid = getattr(ing, "_stock_item_id", None)  # noqa: SLF001
            if sid is not None and not ing.is_optional:
                in_play.add(sid)
                decision_by_item.setdefault(sid, "a meal you've planned this week needs it")

    if not in_play:
        return []

    # ── Compute belief for just the in-play set; ask about the uncertain. ──
    items = repository.get(StockItem).include(StockItem.Fields.STOCK_LEVEL).all(
        EntityField(StockItem, "id").in_(list(in_play))
    )
    beliefs = gather_beliefs_for_items(repository, items)
    name_by_id = {i.id: i.name for i in items}

    candidates: list[tuple[float, UUID]] = []
    for item_id, belief in beliefs.items():
        # "Uncertain enough to be worth a decision-time question": low
        # confidence, or the inference disagrees with the recorded level
        # without being highly confident. High-confidence beliefs (incl.
        # freshly-checked items) never nag.
        uncertain = (
            belief.confidence_band == "low"
            or (belief.differs_from_recorded and belief.confidence_band != "high")
        )
        if uncertain:
            candidates.append((belief.confidence, item_id))

    # Least-confident first; cap so this is a targeted nudge, not a queue.
    candidates.sort(key=lambda t: t[0])
    out: list[Suggestion] = []
    for _confidence, item_id in candidates[:_PANTRY_CHECK_MAX]:
        belief = beliefs[item_id]
        name = name_by_id.get(item_id, "an item")
        why_decision = decision_by_item.get(item_id, "a decision depends on it")
        out.append(Suggestion(
            kind=KIND_PANTRY_CHECK,
            dedup_key=str(item_id),
            severity=SEVERITY_LOW,
            title=f"Still have {name}?",
            body=f"I think it's {belief.believed_band} — {why_decision}. A quick check keeps me honest.",
            reason=(
                f"{belief.reason} Confidence is {belief.confidence_band}, and "
                f"{why_decision}, so a one-tap confirm resolves the uncertainty "
                f"before you rely on it."
            ),
            primary_action={"path": f"/stock/{item_id}", "label": "Quick check"},
            payload={
                "stock_item_id": str(item_id),
                "item_name": name,
                "believed_band": belief.believed_band,
                "confidence": belief.confidence_band,
            },
        ))
    return out


# ── Orchestrator ────────────────────────────────────────────────────────

def generate_all(repository: SqlAlchemyRepository, user_id: UUID | None) -> list[Suggestion]:
    out: list[Suggestion] = []
    out.extend(generate_use_soon(repository))
    out.extend(generate_over_budget(repository, user_id))
    out.extend(generate_likely_due(repository))
    out.extend(generate_frequent_waster(repository))
    out.extend(generate_pantry_check(repository, user_id))
    return out
