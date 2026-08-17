"""Daily-brief wording + policy unit tests (owner call 2026-08-17).

Every test here drives the module-level pure functions with plain fixtures —
no DB, no clock, no push provider — mirroring `test_pantry_belief.py`. The
handler around them is a thin repo walk covered by the e2e suite.

What's pinned:
  • slot ordering follows `MealSlot.sequence`, not insertion or alphabetical
  • the named-meal cap and its "+N more" tail
  • the three-way gap / silence / list branch, which is the whole reason the
    brief is quiet enough to keep notifications on
  • the shopping half's singular-vs-plural phrasing
  • the ledger key is date-scoped (yesterday must not suppress today)
"""
from datetime import date

from dora_api.domain.entities.meal_slot import MealSlot
from dora_api.features.alerts.get_alerts import AlertDto
from dora_api.features.alerts.send_daily_brief import (DAILY_BRIEF_HOUR,
                                                       brief_ledger_key)
from dora_api.features.meal_plans.daily_brief import (MAX_NAMED_MEALS,
                                                      format_meal_line,
                                                      format_shopping_line,
                                                      is_brief_hour,
                                                      slot_order_map)


class _Recipe:
    """Only `.name` is read by the formatter — a stand-in keeps the fixture
    free of the Recipe entity's required fields."""
    def __init__(self, name: str) -> None:
        self.name = name


class _Entry:
    """Matches the `.slot` / `.recipe` shape `format_meal_line` reads."""
    def __init__(self, slot: str, recipe_name: str | None) -> None:
        self.slot = slot
        self.recipe = _Recipe(recipe_name) if recipe_name is not None else None


def _slots(*names: str) -> list[MealSlot]:
    return [MealSlot(name=n, sequence=i) for i, n in enumerate(names)]


_STANDARD_ORDER = slot_order_map(_slots("Breakfast", "Lunch", "Dinner", "Snack"))


def _shopping_alert(message: str) -> AlertDto:
    return AlertDto(
        alert_id="list:abc:shopping_day",
        kind="shopping_day",
        severity="low",
        message=message,
        detail=None,
    )


# ── Slot ordering ───────────────────────────────────────────────────────

def test__slot_order_map__orders_by_sequence_not_alphabetically():
    # "Breakfast" sorts before "Dinner" alphabetically too, so use a
    # vocabulary where sequence and alphabet actively disagree.
    order = slot_order_map(_slots("Dinner", "Breakfast"))
    assert order["dinner"] < order["breakfast"]


def test__slot_order_map__ties_on_sequence_break_alphabetically():
    slots = [MealSlot(name="Supper", sequence=1), MealSlot(name="Brunch", sequence=1)]
    order = slot_order_map(slots)
    assert order["brunch"] < order["supper"]


def test__meal_line__lists_meals_in_slot_order():
    line = format_meal_line(
        [_Entry("Dinner", "Chicken curry"), _Entry("Breakfast", "Porridge")],
        _STANDARD_ORDER,
        week_has_entries=True,
    )
    assert line == "Tomorrow — Breakfast: Porridge; Dinner: Chicken curry."


def test__meal_line__unknown_slot_sorts_last():
    """A slot renamed since the entry was saved isn't in the vocabulary map.
    It must still render — sorted to the end, never dropped or raising."""
    line = format_meal_line(
        [_Entry("Elevenses", "Scones"), _Entry("Breakfast", "Porridge")],
        _STANDARD_ORDER,
        week_has_entries=True,
    )
    assert line == "Tomorrow — Breakfast: Porridge; Elevenses: Scones."


# ── The cap ─────────────────────────────────────────────────────────────

def test__meal_line__caps_named_meals_and_counts_the_rest():
    entries = [
        _Entry("Breakfast", "Porridge"),
        _Entry("Lunch", "Soup"),
        _Entry("Dinner", "Curry"),
        _Entry("Snack", "Apple"),
    ]
    line = format_meal_line(entries, _STANDARD_ORDER, week_has_entries=True)
    assert line == "Tomorrow — Breakfast: Porridge; Lunch: Soup; Dinner: Curry; +1 more."
    assert line.count(";") == MAX_NAMED_MEALS


def test__meal_line__exactly_at_the_cap_has_no_tail():
    entries = [
        _Entry("Breakfast", "Porridge"),
        _Entry("Lunch", "Soup"),
        _Entry("Dinner", "Curry"),
    ]
    line = format_meal_line(entries, _STANDARD_ORDER, week_has_entries=True)
    assert "more" not in line


# ── Gap vs silence — the reason this channel stays bearable ─────────────

def test__meal_line__empty_tomorrow_but_planned_week__nudges_about_the_gap():
    line = format_meal_line([], _STANDARD_ORDER, week_has_entries=True)
    assert line == "Nothing planned for tomorrow yet."


def test__meal_line__empty_tomorrow_and_empty_week__stays_silent():
    """Someone who isn't using the planner this week must not be nagged every
    single evening — that's what turns a useful channel into one you mute."""
    assert format_meal_line([], _STANDARD_ORDER, week_has_entries=False) is None


def test__meal_line__entries_without_a_recipe_are_not_a_meal_line():
    assert format_meal_line(
        [_Entry("Dinner", None)], _STANDARD_ORDER, week_has_entries=True,
    ) is None


# ── Shopping half ───────────────────────────────────────────────────────

def test__shopping_line__none_due__is_silent():
    assert format_shopping_line([]) is None


def test__shopping_line__single__reuses_the_evaluators_message():
    line = format_shopping_line([_shopping_alert("Shopping day tomorrow: Weekly shop")])
    assert line == "Shopping day tomorrow: Weekly shop."


def test__shopping_line__several__summarises_with_a_plural():
    line = format_shopping_line([
        _shopping_alert("Shopping day today: Weekly shop"),
        _shopping_alert("Shopping day tomorrow: Butcher"),
    ])
    assert line == "2 shopping lists due for a shop."


# ── Send-hour gate ──────────────────────────────────────────────────────

def test__is_brief_hour__only_the_configured_hour():
    assert is_brief_hour(DAILY_BRIEF_HOUR, DAILY_BRIEF_HOUR) is True
    assert is_brief_hour(DAILY_BRIEF_HOUR - 1, DAILY_BRIEF_HOUR) is False
    assert is_brief_hour(DAILY_BRIEF_HOUR + 1, DAILY_BRIEF_HOUR) is False


def test__brief_hour_is_evening():
    """Pinned deliberately: a morning brief was considered and rejected —
    by 9am it's too late to take the chicken out."""
    assert 17 <= DAILY_BRIEF_HOUR <= 21


# ── Dedup ledger key ────────────────────────────────────────────────────

def test__ledger_key__is_date_scoped():
    """One row per (user, household date). Without the date, yesterday's
    stamp would suppress every future brief forever."""
    assert brief_ledger_key(date(2026, 8, 18)) != brief_ledger_key(date(2026, 8, 19))
    assert brief_ledger_key(date(2026, 8, 18)).endswith("2026-08-18")


def test__ledger_key__is_stable_for_the_same_day():
    assert brief_ledger_key(date(2026, 8, 18)) == brief_ledger_key(date(2026, 8, 18))
