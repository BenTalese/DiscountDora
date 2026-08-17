"""Regression test for the one bug in the daily brief that fails *silently*.

`MealPlanEntry.recipe` is mapped `lazy="noload"` (R-019 / ADR-014), so a query
that doesn't `.include(MealPlanEntry.Fields.RECIPE)` hands back an entry whose
`recipe` is **None** — no exception, no warning. The first cut of
`daily_brief.py` did exactly that, and the result was a brief that dutifully
fired every evening and never named a single meal. Nothing in the pure-function
tests could catch it, because the bug lives in the repo walk.

So this file exists to pin one thing: the handler's entry read resolves the
recipe. It's cheap to keep and expensive to re-check by hand, which is the bar
`DORA_VERIFY_TRIAGE.md` sets for writing a test at all.

Isolation follows `test_sqlalchemy_repository.py`: DB env vars are pinned to a
throwaway path *before* any dora_api import, and the repository module's `db`
handle is swapped for a stub bound to a private temp engine — so this never
touches the shared e2e database.
"""
import os
import tempfile
from pathlib import Path

# Must run before any dora_api import — dora_api.app resolves the DB URL at
# import time. DORA_DB_URL wins over DORA_DB_PATH, so pin both.
_ISOLATION_DIR = Path(tempfile.mkdtemp(prefix="dora-brief-tests-"))
os.environ["DORA_DB_PATH"] = str(_ISOLATION_DIR / "never-opened.db")
os.environ["DORA_DB_URL"] = f"sqlite:///{(_ISOLATION_DIR / 'never-opened.db').as_posix()}"

from datetime import date, datetime  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from uuid import UUID  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy import inspect as sa_inspect  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import dora_api.persistence.sqlalchemy_repository as repo_module  # noqa: E402
from dora_api.domain.entities.meal_plan import MealPlan  # noqa: E402
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry  # noqa: E402
from dora_api.domain.entities.meal_slot import MealSlot  # noqa: E402
from dora_api.domain.entities.recipe import Recipe  # noqa: E402
from dora_api.features.alerts.get_alerts import AlertsDto  # noqa: E402
from dora_api.features.meal_plans.daily_brief import \
    BuildDailyBriefHandler  # noqa: E402
from dora_api.persistence.sqlalchemy_repository import \
    SqlAlchemyRepository  # noqa: E402


_TODAY = date(2026, 8, 17)
_TOMORROW = date(2026, 8, 18)
_USER = UUID(int=900)


def _uid(n: int) -> UUID:
    return UUID(int=n)


def _recipe(name: str, rid: UUID) -> Recipe:
    return Recipe(
        id=rid, name=name, available_meals=0, category=None,
        cook_time_minutes=None, cuisine=None, difficulty=None, image=None,
        ingredients=[], instructions=None, is_favourite=False,
        last_made_on=None, prep_time_minutes=None, recipe_collection=None,
        servings=None, source=None, time_of_day=None, version_group_id=None,
        kcal=None, steps_mode="freeform", created_at=datetime(2026, 8, 1),
    )


class _NoAlerts:
    """Stub for the alerts evaluator — this file is about the meal read, and
    standing up the full alert surface would drag in a dozen unrelated tables.
    Injectable precisely so this stays possible."""
    def handle(self, user_id):  # noqa: ARG002
        return AlertsDto()


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("brief-db") / "brief_tests.db"
    eng = create_engine(f"sqlite:///{db_path.as_posix()}")
    sa_inspect(MealPlanEntry).local_table.metadata.create_all(eng)

    with Session(eng) as seed:
        seed.add_all([
            MealSlot(id=_uid(1), name="Breakfast", sequence=0),
            MealSlot(id=_uid(2), name="Dinner", sequence=2),
        ])
        curry = _recipe("Chicken curry", _uid(10))
        porridge = _recipe("Porridge", _uid(11))
        seed.add_all([curry, porridge])
        seed.flush()
        plan = MealPlan(
            id=_uid(20), entries=[], name=None, start_date=_TODAY,
        )
        seed.add(plan)
        seed.flush()
        plan.entries = [
            MealPlanEntry(
                id=_uid(30), recipe=curry, scheduled_for=_TOMORROW,
                servings=2, slot="Dinner",
            ),
            MealPlanEntry(
                id=_uid(31), recipe=porridge, scheduled_for=_TOMORROW,
                servings=2, slot="Breakfast",
            ),
        ]
        seed.commit()

    yield eng
    eng.dispose()


@pytest.fixture()
def repo(engine, monkeypatch):
    session = Session(engine)
    monkeypatch.setattr(repo_module, "db", SimpleNamespace(session=session))
    yield SqlAlchemyRepository()
    session.rollback()
    session.close()


def test__entries_read__resolves_the_recipe_relationship(repo):
    """The R-019 trap. Without `.include(...)` every `recipe` here is None and
    the brief silently loses its entire reason to exist."""
    entries = BuildDailyBriefHandler(repo)._entries_between(_TOMORROW, _TOMORROW)

    assert len(entries) == 2
    assert all(e.recipe is not None for e in entries), (
        "MealPlanEntry.recipe is lazy='noload' — the query must .include() it"
    )
    assert {e.recipe.name for e in entries} == {"Chicken curry", "Porridge"}


def test__brief__names_tomorrows_meals_in_slot_order(repo):
    brief = BuildDailyBriefHandler(repo, alerts_handler=_NoAlerts()).handle(
        user_id=_USER, today=_TODAY,
    )

    assert brief.is_empty is False
    # Breakfast (sequence 0) before Dinner (sequence 2).
    assert brief.meal_line == "Tomorrow — Breakfast: Porridge; Dinner: Chicken curry."
    assert brief.body == brief.meal_line


def test__brief__day_with_no_meals_and_no_shopping__is_silent(repo):
    """`today` two days out puts "tomorrow" past every seeded entry and
    outside the planning window, so the brief must not fire at all."""
    brief = BuildDailyBriefHandler(repo, alerts_handler=_NoAlerts()).handle(
        user_id=_USER, today=date(2026, 9, 30),
    )

    assert brief.is_empty is True
    assert brief.body == ""
