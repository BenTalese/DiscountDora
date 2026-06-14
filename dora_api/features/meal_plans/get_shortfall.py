import logging
from dataclasses import dataclass
from datetime import date
from typing import List
from uuid import UUID

from sqlalchemy import text

from dora_api.app import db
from dora_api.features.app_settings.clock import household_today
from dora_api.features.routers import MEAL_PLAN_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


def _coerce_uuid(value) -> UUID:
    """UUIDType columns are 16-byte BLOBs in SQLite; raw text() reads
    return them as bytes. Normalise back to a UUID object so DTOs and
    JSON serialisation behave."""
    if isinstance(value, UUID):
        return value
    if isinstance(value, bytes):
        return UUID(bytes=value)
    return UUID(str(value))


@dataclass(frozen=True, slots=True)
class ShortfallDto:
    recipe_id: UUID
    recipe_name: str
    available_meals: int
    committed_meals: int
    shortfall: int
    earliest_needed: date | None


class GetShortfallHandler:
    def handle(self) -> List[ShortfallDto]:
        # For every recipe with at least one un-consumed future entry,
        # compare its pool to the sum of committed servings. Anything
        # where commitments outstrip the pool is a shortfall the user
        # needs to cook before `earliest_needed`.
        _Today = household_today(SqlAlchemyRepository())
        _Rows = db.session.execute(
            text(
                "SELECT r.id, r.name, r.available_meals, "
                "       SUM(e.servings) AS committed, "
                "       MIN(e.scheduled_for) AS earliest "
                'FROM "Recipe" r '
                'JOIN "MealPlanEntry" e ON e.recipe_id = r.id '
                "WHERE e.consumed_at IS NULL AND e.scheduled_for >= :today "
                "GROUP BY r.id, r.name, r.available_meals "
                "HAVING SUM(e.servings) > r.available_meals"
            ),
            {"today": _Today},
        ).all()

        _Out: List[ShortfallDto] = []
        for _RecipeId, _Name, _Available, _Committed, _Earliest in _Rows:
            _Out.append(ShortfallDto(
                recipe_id = _coerce_uuid(_RecipeId),
                recipe_name = _Name,
                available_meals = _Available,
                committed_meals = int(_Committed or 0),
                shortfall = int(_Committed or 0) - int(_Available or 0),
                earliest_needed = _Earliest,
            ))
        return _Out


@MEAL_PLAN_ROUTER.route("shortfall")
def get_shortfall():
    _Logger = logging.getLogger(__name__)
    _Result = GetShortfallHandler().handle()
    _Logger.info(f"Shortfall report: {len(_Result)} recipes need cooking")
    return ok(_Result)
