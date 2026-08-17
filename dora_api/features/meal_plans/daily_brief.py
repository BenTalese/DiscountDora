"""The daily brief — what tomorrow looks like, in one notification.

Owner call 2026-08-17. The original ask was per-slot cooking reminders driven
by a slot start time. That was costed and rejected in favour of this: five
slots across seven days is up to **35 notifications a week**, which trains the
user to ignore the channel (Charter P10 Anti-creep). One evening brief is at
most 7, and is silent on days with nothing to say — so fewer in practice.

Two consequences worth knowing, because they're why this module is so small:

  * **`MealSlot` needs no start time.** A brief covering a whole day never
    asks "is dinner soon?", so slots are ordered by the `sequence` they
    already have. No migration, no time inputs, no per-slot timezone maths.
  * **The just-in-time nudge is a won't-do**, not a deferral (owner: "they
    know when dinner is"). Don't reintroduce slot times for it later without
    revisiting that call.

Content, in order:
  1. Tomorrow's planned meals (or the gap nudge — see `format_meal_line`).
  2. Any shopping day that's due, read from the canonical alerts evaluator so
     the brief and the bell can never disagree (R-003).

Structure: the wording rules are **module-level pure functions** taking plain
data, and the handler is a thin repo walk that calls them — matching
`pantry_belief.compute_belief` / `off_lookup._parse_off_response`. Every
interesting rule (slot ordering, the cap, the gap-vs-silence branch) is
therefore unit-testable with no DB, no clock and no push provider.

Delivery — when it fires, dedup, who gets it — is
`features/alerts/send_daily_brief.py`. This module never sends or stamps.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, List, Sequence
from uuid import UUID

from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.meal_slot import MealSlot
from dora_api.features.alerts.get_alerts import AlertDto, GetAlertsHandler
from dora_api.infrastructure.ports import Repository
from dora_api.infrastructure.utils import pluralize
from dora_api.persistence.field import EntityField


# The "is this household actually planning?" window. If tomorrow is empty we
# only nudge about the gap when there are entries somewhere in the next
# `PLANNING_WINDOW_DAYS` — otherwise we'd nag someone who simply isn't using
# the planner this week, every single evening.
PLANNING_WINDOW_DAYS = 7

# A notification that needs scrolling has already failed. Cap the named meals
# and roll the rest into "+N more".
MAX_NAMED_MEALS = 3

SHOPPING_DAY_KIND = "shopping_day"


@dataclass(frozen=True, slots=True)
class DailyBrief:
    """The assembled brief. `is_empty` is the silence gate — the owner was
    explicit that a brief with nothing to say must not fire, because a
    notification arriving every day regardless is one you learn to swipe away
    without reading, which costs us the evenings it did matter."""
    title: str
    body: str
    url: str
    # Held separately from `body` so each half can be asserted on its own, and
    # so another channel (an in-app card, an email section) could lay them out
    # differently without re-deriving them.
    meal_line: str | None
    shopping_line: str | None

    @property
    def is_empty(self) -> bool:
        return self.meal_line is None and self.shopping_line is None


# ── Pure wording rules ───────────────────────────────────────────────

def slot_order_map(slots: Iterable[MealSlot]) -> dict[str, int]:
    """Slot name (lowercased) → display position. Mirrors the ordering
    `GetMealSlotsHandler` applies, so the brief lists tomorrow in the same
    order the planner shows it."""
    ordered = sorted(slots, key=lambda s: (s.sequence, s.name.lower()))
    return {s.name.lower(): i for i, s in enumerate(ordered)}


def format_meal_line(
    tomorrows_entries: Sequence[MealPlanEntry],
    slot_order: dict[str, int],
    week_has_entries: bool,
) -> str | None:
    """Tomorrow's meals in slot order. Three outcomes:

      * entries exist          → name them ("Dinner: Chicken curry").
      * none, week has some    → the gap nudge. This is the batch-mode
                                 "the slot's coming and nothing's allocated"
                                 case at day granularity instead of slot —
                                 same job, a fraction of the noise.
      * none, week is empty    → **None**. They aren't planning this week;
                                 nagging every evening would be pure noise.
    """
    if not tomorrows_entries:
        return "Nothing planned for tomorrow yet." if week_has_entries else None

    # Unknown slots sort last but stay stable among themselves.
    # `MealPlanEntry.slot` is free text validated against the vocabulary at
    # write time, so a slot renamed since the entry was saved lands here
    # rather than raising.
    ordered = sorted(
        tomorrows_entries,
        key=lambda e: (slot_order.get(e.slot.lower(), len(slot_order)), e.slot.lower()),
    )
    named = [e for e in ordered if e.recipe is not None][:MAX_NAMED_MEALS]
    if not named:
        return None
    parts = [f"{e.slot}: {e.recipe.name}" for e in named]
    remainder = len(ordered) - len(named)
    if remainder > 0:
        parts.append(f"+{remainder} more")
    return "Tomorrow — " + "; ".join(parts) + "."


def format_shopping_line(shopping_alerts: Sequence[AlertDto]) -> str | None:
    """One line for any shopping day that's due. The single-alert case reuses
    the evaluator's own message, which already carries the list name and the
    when ("Shopping day tomorrow: Weekly shop")."""
    if not shopping_alerts:
        return None
    if len(shopping_alerts) == 1:
        return f"{shopping_alerts[0].message}."
    count = len(shopping_alerts)
    return f"{count} {pluralize(count, 'shopping list')} due for a shop."


def is_brief_hour(hour: int, brief_hour: int) -> bool:
    """Trivial, but named so the job reads as intent and the boundary gets a
    test. Lives here with the rest of the brief's policy; the job owns
    delivery only."""
    return hour == brief_hour


# ── Repo walk ────────────────────────────────────────────────────────

class BuildDailyBriefHandler:
    def __init__(
        self,
        repository: Repository,
        alerts_handler: GetAlertsHandler | None = None,
    ) -> None:
        self.repository = repository
        # Injected rather than constructed inline so a caller (and a test) can
        # supply a stub. Defaults to the canonical evaluator — the brief must
        # not grow its own idea of what "shopping day" means (R-003).
        self.alerts_handler = alerts_handler or GetAlertsHandler(repository)

    def handle(self, user_id: UUID, today: date) -> DailyBrief:
        """Assemble the brief for the evening of `today`, describing
        **tomorrow**. `today` is the caller's household-local date (R-021) —
        this handler never reads the clock, which is what lets it be tested
        without freezing time."""
        tomorrow = today + timedelta(days=1)

        entries = self._entries_between(tomorrow, tomorrow)
        window_end = tomorrow + timedelta(days=PLANNING_WINDOW_DAYS - 1)
        # Only needed to decide gap-vs-silence, so skip the second read
        # entirely when tomorrow already has meals.
        week_has_entries = bool(entries) or bool(
            self._entries_between(tomorrow, window_end, with_recipe=False)
        )

        meal_line = format_meal_line(
            entries,
            slot_order_map(self.repository.get(MealSlot).all()),
            week_has_entries,
        )
        shopping_line = format_shopping_line(self._shopping_alerts(user_id))

        body = " ".join(part for part in (meal_line, shopping_line) if part)
        return DailyBrief(
            title="Tomorrow at a glance",
            body=body,
            # Deep-links to the planner: the meal half is the headline and
            # also where you'd act on a gap. The shopping half names its list
            # in the text, and the bell already carries a per-list link.
            url="/meal-plans",
            meal_line=meal_line,
            shopping_line=shopping_line,
        )

    def _entries_between(
        self, start: date, end: date, with_recipe: bool = True,
    ) -> List[MealPlanEntry]:
        """R-019 / ADR-014 — `MealPlanEntry.recipe` is mapped `lazy="noload"`,
        so it comes back **None** unless the query explicitly includes it. That
        fails silently rather than raising, which is exactly how the first cut
        of this module produced a brief that never named a single meal. The
        planning-window probe passes `with_recipe=False`: it only counts rows,
        so joining Recipe for it would be waste."""
        query = self.repository.get(MealPlanEntry)
        if with_recipe:
            query = query.include(MealPlanEntry.Fields.RECIPE)
        return list(query.all(
            EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR)
            .between(start, end)
        ))

    def _shopping_alerts(self, user_id: UUID) -> List[AlertDto]:
        """Shopping-day alerts from the canonical evaluator, so a user who has
        *disabled* that kind in their alert preferences — or snoozed the
        specific list — correctly gets no shopping half in their brief. Only
        `items` (active) is read; snoozed and dismissed are excluded upstream.
        """
        alerts = self.alerts_handler.handle(user_id=user_id)
        return [a for a in alerts.items if a.kind == SHOPPING_DAY_KIND]
