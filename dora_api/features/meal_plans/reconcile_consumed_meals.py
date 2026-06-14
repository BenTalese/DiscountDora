from datetime import UTC, datetime

from sqlalchemy import text

from dora_api.app import db
from dora_api.features.app_settings.clock import today_in_timezone


def reconcile_consumed_meals() -> None:
    """Mark past-day meal-plan entries as consumed and decrement the
    Recipe pool counts they drew from.

    Runs in its own connection-level transaction, deliberately decoupled
    from the per-request ORM session. The reconciliation result is
    independently correct — a handler rolling back its work shouldn't
    also undo the day's consumption sweep, and a slow request shouldn't
    hold the reconciliation open inside the same transaction.

    Idempotent via the conditional UPDATE ... RETURNING: any concurrent
    caller racing on the same entry will get zero rows and skip the
    decrement. Floors `available_meals` at zero — a slot that's planned
    without anything in the pool just locks read-only.
    """
    _Now = datetime.now(UTC)

    with db.engine.begin() as _Conn:
        # Evaluate the "past day" boundary in the household timezone (C-2.K),
        # not server-local — read it on this same connection to stay decoupled
        # from the per-request ORM session. No row yet ⇒ UTC default.
        _TzRow = _Conn.execute(text('SELECT timezone FROM "AppSetting" LIMIT 1')).first()
        _Today = today_in_timezone(_TzRow[0] if _TzRow else None)
        _Consumed = _Conn.execute(
            text(
                'UPDATE "MealPlanEntry" '
                "SET consumed_at = :now "
                "WHERE scheduled_for < :today AND consumed_at IS NULL "
                "RETURNING recipe_id, servings"
            ),
            {"now": _Now, "today": _Today},
        ).all()

        if not _Consumed:
            return

        _Totals: dict = {}
        for _RecipeId, _Servings in _Consumed:
            _Totals[_RecipeId] = _Totals.get(_RecipeId, 0) + (_Servings or 0)

        for _RecipeId, _ToDecrement in _Totals.items():
            # _RecipeId may be bytes (UUIDType stored as 16-byte BLOB in
            # SQLite); the column is binary, so feed it back as bytes
            # when we got bytes, otherwise as a UUID string. Both work;
            # passing a raw uuid.UUID does not.
            _Bind = _RecipeId if isinstance(_RecipeId, bytes) else str(_RecipeId)
            _Conn.execute(
                text(
                    'UPDATE "Recipe" '
                    "SET available_meals = CASE "
                    "  WHEN available_meals - :n < 0 THEN 0 "
                    "  ELSE available_meals - :n "
                    "END "
                    "WHERE id = :rid"
                ),
                {"n": _ToDecrement, "rid": _Bind},
            )
