"""Print-view export for meal plans (weekly calendar).

  GET /api/meal-plans/<id>/print-view

CSV export was removed (FU-168) — a meal plan is a calendar, not a tabular
dataset, so CSV added no real value; print-view (→ "Save as PDF") covers the
export need.
"""
from collections import defaultdict
from datetime import date, datetime, timezone
from uuid import UUID

from flask import Response, render_template_string

from dora_api.features.data.export_shared import PRINT_CSS, PRINT_TOOLBAR
from dora_api.features.meal_plans.get_meal_plans import (
    GetMealPlansHandler, MealPlanDto,
)
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import not_found
from dora_api.infrastructure.utils import get_container


# Conventional meal slots; entries with unrecognised slots fall into "Other"
# and get rendered alphabetically.
_KNOWN_SLOTS = ("Breakfast", "Lunch", "Dinner", "Snack")


_PRINT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{{ plan.name }} · meal plan</title>
  {{ css | safe }}
  <style>
    table.calendar { border-collapse: separate; border-spacing: 0; width: 100%; }
    table.calendar th { background: #f4f4f4; }
    table.calendar td, table.calendar th {
      border: 1px solid #ddd; padding: 6px 8px; vertical-align: top;
      font-size: 12px;
    }
    .day-header { font-weight: 600; }
    .day-subheader { color: #666; font-size: 11px; }
    .entry { margin: 2px 0; padding: 3px 5px; background: #fafafa; border-radius: 4px; }
    .entry .slot { font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.04em; }
    .entry .meal { font-weight: 500; }
    .entry .servings { color: #666; font-size: 10px; }
  </style>
</head>
<body>
  {{ toolbar | safe }}
  <div class="page">
    <h1>{{ plan.name }}</h1>
    <div class="meta">
      Generated {{ generated_at }} · starts {{ plan.start_date }} ·
      {{ plan.entries | length }} entr(y/ies)
    </div>

    {% if plan.entries | length == 0 %}
      <p><em>No meals scheduled yet.</em></p>
    {% else %}
      <table class="calendar">
        <thead>
          <tr>
            <th>Date</th>
            {% for slot in slot_order %}
              <th>{{ slot }}</th>
            {% endfor %}
          </tr>
        </thead>
        <tbody>
          {% for day, entries_by_slot in days %}
            <tr>
              <td>
                <div class="day-header">{{ day.strftime('%a %d %b') }}</div>
              </td>
              {% for slot in slot_order %}
                <td>
                  {% for entry in entries_by_slot.get(slot, []) %}
                    <div class="entry">
                      <div class="meal">{{ entry.recipe_name }}</div>
                      <div class="servings">
                        {{ entry.servings }} serving(s)
                      </div>
                    </div>
                  {% endfor %}
                </td>
              {% endfor %}
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% endif %}
  </div>
</body>
</html>
"""


def _render_print_view(plan: MealPlanDto) -> str:
    # Group entries by day, then by slot. Slot column order is the
    # _KNOWN_SLOTS list followed by any unrecognised slot the plan uses
    # (alphabetised, surfaced after the conventional ones).
    days_map: dict[date, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    unrecognised: set[str] = set()
    for entry in plan.entries:
        days_map[entry.scheduled_for][entry.slot].append(entry)
        if entry.slot not in _KNOWN_SLOTS:
            unrecognised.add(entry.slot)

    slot_order = list(_KNOWN_SLOTS) + sorted(unrecognised)
    days = sorted(days_map.items(), key=lambda kv: kv[0])

    generated_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    return render_template_string(
        _PRINT_TEMPLATE,
        plan=plan,
        days=days,
        slot_order=slot_order,
        generated_at=generated_at,
        css=PRINT_CSS,
        toolbar=PRINT_TOOLBAR,
    )


@MEAL_PLAN_ROUTER.route("/<meal_plan_id>/print-view", methods=["GET"])
def print_view_meal_plan(meal_plan_id: UUID):
    plan = get_container().inject(GetMealPlansHandler).handle_by_id(meal_plan_id)
    if plan is None:
        return not_found("MealPlan", meal_plan_id)
    html = _render_print_view(plan)
    return Response(html, mimetype="text/html; charset=utf-8")
