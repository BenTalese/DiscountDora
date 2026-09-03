import uuid
from datetime import UTC, datetime

from sqlalchemy import text

from dora_api.app import db
from dora_api.domain.entities.meal_plan_reconcile_receipt import (
    STATE_UNRESOLVED_AUTO, STATE_UNRESOLVED_MANUAL)
from dora_api.features.app_settings.clock import today_in_timezone
from dora_api.features.recipes.pool import bump_pool


def reconcile_consumed_meals() -> None:
    """FU-317 Chunk 1 — daily meal-plan reconcile sweep.

    Runs in its own connection-level transaction, deliberately decoupled
    from the per-request ORM session. A handler rolling back its work
    shouldn't also undo the day's consumption sweep; a slow request
    shouldn't hold the reconciliation open inside the same transaction.

    Two branches, driven by the install-wide `AppSetting.auto_drain_past_meals`
    posture (D5 install-wide — FU-517 resolved 2026-07-09).

    - **auto-drain ON (default).** Today's behaviour: past-day entries
      with `consumed_at IS NULL` stamp `consumed_at = now()` and the
      `Recipe.available_meals` pool is decremented (floored at 0).
      **New:** every drained entry gets an `unresolved_auto`
      `MealPlanReconcileReceipt`, so the user can walk `/meal-plans/
      reconcile` and dispute per-entry. Idempotence via the conditional
      UPDATE ... RETURNING: a concurrent caller racing on the same entry
      gets zero rows and skips the decrement + receipt.

    - **auto-drain OFF.** The sweep **does not** touch `MealPlanEntry.
      consumed_at` or `Recipe.available_meals` — the reconcile page
      becomes the mutation surface. For each past-day, unconsumed entry
      that doesn't already have an unresolved receipt, an
      `unresolved_manual` receipt is written. `NOT EXISTS` de-dupes so
      the sweep is idempotent across days.
    """
    _Now = datetime.now(UTC)

    with db.engine.begin() as _Conn:
        # Read the two install-wide knobs on this same connection — one
        # round-trip. Timezone drives the "today" boundary; auto_drain_past_meals
        # drives which branch runs. Absent row ⇒ defaults (UTC + drain on).
        _SettingRow = _Conn.execute(
            text('SELECT timezone, auto_drain_past_meals FROM "AppSetting" LIMIT 1')
        ).first()
        _Tz = _SettingRow[0] if _SettingRow else None
        # SQLite stores booleans as 0/1; both branches truthy-check safely.
        _AutoDrain = bool(_SettingRow[1]) if _SettingRow else True
        _Today = today_in_timezone(_Tz)

        if _AutoDrain:
            _sweep_auto_drain(_Conn, _Now, _Today)
        else:
            _sweep_manual_confirm(_Conn, _Now, _Today)


def _sweep_auto_drain(_Conn, _Now: datetime, _Today) -> None:
    """auto-drain ON branch — the historic behaviour + a receipt per drain.

    The `NOT EXISTS` guard mirrors the manual branch: once a user has made
    a decision via the reconcile page (any receipt, resolved or not), the
    sweep must not re-touch the entry. Without this, a `Didn't cook` verb
    that clears `consumed_at` would trigger the next sweep to re-drain
    the pool + write a fresh `unresolved_auto` receipt on top of the
    user's `resolved_not_cooked` decision.

    A `cook_fresh` entry is drained of nothing — see the `_Totals` loop.
    """
    _Consumed = _Conn.execute(
        text(
            'UPDATE "MealPlanEntry" '
            "SET consumed_at = :now "
            "WHERE id IN ("
            '  SELECT mpe.id FROM "MealPlanEntry" mpe '
            "  WHERE mpe.scheduled_for < :today "
            "    AND mpe.consumed_at IS NULL "
            "    AND NOT EXISTS ("
            '      SELECT 1 FROM "MealPlanReconcileReceipt" r '
            "      WHERE r.meal_plan_entry_id = mpe.id"
            "    )"
            ") "
            "RETURNING id, recipe_id, servings, cook_fresh"
        ),
        {"now": _Now, "today": _Today},
    ).all()

    if not _Consumed:
        return

    for _EntryId, _RecipeId, _Servings, _CookFresh in _Consumed:
        _insert_receipt(
            _Conn, _EntryId, STATE_UNRESOLVED_AUTO,
            original_servings=int(_Servings or 0), created_at=_Now,
        )

    # A meal marked cooked-fresh was cooked on its day and eaten off the stove,
    # so nothing left the pool — draining one would silently destroy a portion
    # the household still has (owner 2026-09-04). It is still consumed and
    # still gets a receipt; only the pool arithmetic skips it.
    _Totals: dict = {}
    for _EntryId, _RecipeId, _Servings, _CookFresh in _Consumed:
        if bool(_CookFresh):
            continue
        _Totals[_RecipeId] = _Totals.get(_RecipeId, 0) + int(_Servings or 0)

    for _RecipeId, _ToDecrement in _Totals.items():
        # FU-317 Chunk 2 — one authority for pool math (see recipes/pool.py).
        # Passing the sweep's own `_Conn` keeps the decrement in this
        # decoupled connection-level transaction, not the per-request
        # ORM session.
        bump_pool(_RecipeId, -_ToDecrement, connection=_Conn)


def _sweep_manual_confirm(_Conn, _Now: datetime, _Today) -> None:
    """auto-drain OFF branch — write `unresolved_manual` receipts only.

    Past-day entries with `consumed_at IS NULL` that don't already have
    a receipt get one. `MealPlanEntry.consumed_at` and
    `Recipe.available_meals` are deliberately untouched — the reconcile
    page owns those mutations now.
    """
    _Pending = _Conn.execute(
        text(
            'SELECT id, servings FROM "MealPlanEntry" mpe '
            'WHERE mpe.scheduled_for < :today '
            '  AND mpe.consumed_at IS NULL '
            '  AND NOT EXISTS ('
            '    SELECT 1 FROM "MealPlanReconcileReceipt" r '
            '    WHERE r.meal_plan_entry_id = mpe.id'
            '  )'
        ),
        {"today": _Today},
    ).all()

    for _EntryId, _Servings in _Pending:
        _insert_receipt(
            _Conn, _EntryId, STATE_UNRESOLVED_MANUAL,
            original_servings=int(_Servings or 0), created_at=_Now,
        )


def _insert_receipt(_Conn, _EntryId, _State: str, *,
                    original_servings: int, created_at: datetime) -> None:
    # `_EntryId` may arrive as bytes (SQLite BINARY(16)) or str/UUID; feed it
    # back in the same shape (same pattern as the Recipe.id bind above).
    _EntryBind = _EntryId if isinstance(_EntryId, bytes) else str(_EntryId)
    _Conn.execute(
        text(
            'INSERT INTO "MealPlanReconcileReceipt" '
            '(id, meal_plan_entry_id, state, original_servings, created_at) '
            'VALUES (:id, :entry_id, :state, :servings, :created_at)'
        ),
        {
            "id": str(uuid.uuid4()),
            "entry_id": _EntryBind,
            "state": _State,
            "servings": original_servings,
            "created_at": created_at,
        },
    )
