"""GET /api/alerts — items that need the user's attention right now.

All signals are derived from existing schema (expiry_date, stock_level,
is_flagged, plus the stocktake queue's band-based resolver), so the
alert *conditions* are never stored — they're recomputed every request
and so always reflect current pantry state. `stocktake_overdue` alerts
route through the same `resolve_overdue_map` helper the queue endpoint
uses, so the bell + the runner surface the identical set of items
(R-003, single source of truth for "overdue for a check").

What *is* persisted (C-9.1) is each user's *decisions* about an alert —
read / snooze / dismiss — in `AlertInteraction`, keyed by the alert's
stable `<scope>:<id>:<kind>` key. This handler overlays the requesting
user's interactions so the badge, the bell list, the page, and (later)
the channels all agree on one definition of "what counts":

  - dismissed  → hidden everywhere.
  - snoozed    → moved to the `snoozed` list, out of the active counts.
  - everything else → `items`, with `read` stamped.

The badge counts the **actionable** tier; the **FYI** tier is shown in the
list but never inflates it — the rule is explicit (`actionable_count` == the
active actionable-tier list), not a silent exclusion. By default a kind's tier
follows its severity (high/medium → actionable, low → FYI, PROPOSAL_ALERTS §5),
but C-9.2 lets each user override a kind's tier (or disable the kind entirely)
via `AlertPreference`, so the count is computed from the effective per-user tier.

Severity stays one of "high" / "medium" / "low" so the UI can sort/colour
without having to recompute the weight; `tier` is the (possibly overridden)
actionable/FYI bucket the counts use.
"""
import logging
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from typing import List
from uuid import UUID

from flask import session

from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.domain.entities.alert_preference import AlertPreference
from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.meal_plan_entry import MealPlanEntry
from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import (effective_expiring_soon_window,
                                          is_low_stock, is_out_of_stock)
from dora_api.features.alerts.alert_key import (list_alert_key, meal_alert_key,
                                                stock_alert_key)
from dora_api.features.alerts.alert_kinds import (TIER_ACTIONABLE,
                                                  default_tier_for)
from dora_api.features.app_settings.clock import household_today
from dora_api.features.routers import ALERT_ROUTER
from dora_api.features.stocktake.stocktake import resolve_overdue_map
from dora_api.infrastructure.api_response import ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# Severities are an ordinal scale — the UI sorts high first, then medium,
# then low. The bell *badge* counts the actionable tier (high+medium); low
# is FYI and shown but not counted into the badge (PROPOSAL_ALERTS §3.4).
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

_SEVERITY_ORDER = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}

# how soon a list's planned shop date must be to nudge. A small
# constant default (not yet admin-tunable — these are FYI nudges, and per-user
# on/off already covers "I don't want this"); one source here (R-003).
SHOPPING_DAY_WINDOW_DAYS = 3


def _iso_week_label(day: date) -> str:
    """Stable ``YYYY-Www`` label for the ISO week containing ``day`` — the
    no_planned_meals discriminator, so the key matches across evaluations
    within the same week (ledger discipline, alert_key.py)."""
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


@dataclass(frozen=True, slots=True)
class AlertDto:
    # Stable scoped key `<scope>:<id>:<kind>` (alert_key) — the frontend
    # treats it as an opaque id and posts it back to the snooze/read/dismiss
    # endpoints. Named `alert_id` for frontend continuity; its *value* is the
    # generalised key (alert_key.py).
    alert_id: str
    # 'expired' | 'expiring_soon' | 'out_of_stock' | 'low_stock' |
    # 'stocktake_overdue' | 'essential_low' | 'no_planned_meals' | 'shopping_day'
    kind: str
    severity: str
    message: str
    detail: str | None
    # Stock-scoped alerts carry the owning item; the C-9.4 non-stock kinds
    # (no_planned_meals / shopping_day) leave these None.
    stock_item_id: UUID | None = None
    stock_item_name: str | None = None
    # Deep-link target id for non-stock kinds (e.g. the shopping list uuid for
    # shopping_day). The client maps kind + this id to a route; None when the
    # kind links to a fixed page (no_planned_meals → the planner).
    target_id: str | None = None
    # ISO date string (if relevant — e.g. expiry alerts include the date).
    related_date: str | None = None
    # Per-user interaction overlay (C-9.1). `read` reflects this user; for an
    # active (non-snoozed) alert `snoozed_until` is None.
    read: bool = False
    snoozed_until: str | None = None
    # Effective tier (C-9.2): 'actionable' (counts toward the badge) or 'fyi'.
    # Per-kind default (§5), overridable per user via AlertPreference.
    tier: str = TIER_ACTIONABLE


@dataclass(frozen=True, slots=True)
class AlertsDto:
    items: List[AlertDto] = field(default_factory=list)      # active (not snoozed, not dismissed)
    snoozed: List[AlertDto] = field(default_factory=list)    # snoozed by this user (not dismissed)
    # Active-set severity counts (for the "X high · Y medium · Z low" caption).
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    # The canonical numbers (PROPOSAL_ALERTS §3.4):
    actionable_count: int = 0  # active actionable-tier — drives the bell badge
    fyi_count: int = 0         # active FYI-tier
    snoozed_count: int = 0


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


def _active_snooze_until(interaction: AlertInteraction | None, now: datetime) -> datetime | None:
    """The snooze cutoff if it's still in the future, else None."""
    if interaction is None or interaction.snoozed_until is None:
        return None
    until = interaction.snoozed_until
    if until.tzinfo is None:  # SQLite may hand back naive datetimes
        until = until.replace(tzinfo=timezone.utc)
    return until if until > now else None


class GetAlertsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, user_id: UUID | None = None) -> AlertsDto:
        items: List[StockItem] = (
            self.repository.get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .all()
        )
        # R-021 — calendar boundaries evaluate in the household timezone.
        today = household_today(self.repository)
        now = datetime.now(timezone.utc)

        # Household-wide threshold (C-9.2): the expiring-soon window resolves
        # from AppSetting, falling back to the seeded default — one source
        # (R-003), never a second literal 7 here.
        settings: List[AppSetting] = self.repository.get(AppSetting).all()
        window = effective_expiring_soon_window(settings[0] if settings else None)

        # Build the raw alert set (conditions, no counting yet — counts are
        # derived after the per-user interaction + preference overlay).
        raw: List[AlertDto] = []

        for item in items:
            # ── Expiry ─────────────────────────────────────────────────
            if item.expiry_date is not None:
                days_remaining = (item.expiry_date - today).days
                if days_remaining < 0:
                    raw.append(AlertDto(
                        alert_id = stock_alert_key(item.id, "expired"),
                        kind = "expired",
                        severity = SEVERITY_HIGH,
                        stock_item_id = item.id,
                        stock_item_name = item.name,
                        message = f"{item.name} has expired",
                        detail = f"Expired {abs(days_remaining)} day(s) ago.",
                        related_date = item.expiry_date.isoformat(),
                    ))
                elif days_remaining <= window:
                    raw.append(AlertDto(
                        alert_id = stock_alert_key(item.id, "expiring_soon"),
                        kind = "expiring_soon",
                        severity = SEVERITY_MEDIUM,
                        stock_item_id = item.id,
                        stock_item_name = item.name,
                        message = f"{item.name} expires soon",
                        detail = (
                            f"Expires today."
                            if days_remaining == 0
                            else f"Expires in {days_remaining} day(s)."
                        ),
                        related_date = item.expiry_date.isoformat(),
                    ))

            # ── Stock level ────────────────────────────────────────────
            if item.stock_level is not None:
                if is_out_of_stock(item.stock_level):
                    # Essential + out-of-stock is the harshest combination,
                    # so it gets its own kind.
                    if item.is_flagged:
                        raw.append(AlertDto(
                            alert_id = stock_alert_key(item.id, "essential_out"),
                            kind = "essential_low",
                            severity = SEVERITY_HIGH,
                            stock_item_id = item.id,
                            stock_item_name = item.name,
                            message = f"Essential {item.name} is out of stock",
                            detail = "Add it to your shopping list — you've flagged this as essential.",
                            related_date = None,
                        ))
                    else:
                        raw.append(AlertDto(
                            alert_id = stock_alert_key(item.id, "out_of_stock"),
                            kind = "out_of_stock",
                            severity = SEVERITY_MEDIUM,
                            stock_item_id = item.id,
                            stock_item_name = item.name,
                            message = f"{item.name} is out of stock",
                            detail = None,
                            related_date = None,
                        ))
                elif is_low_stock(item.stock_level):
                    if item.is_flagged:
                        raw.append(AlertDto(
                            alert_id = stock_alert_key(item.id, "essential_low"),
                            kind = "essential_low",
                            severity = SEVERITY_HIGH,
                            stock_item_id = item.id,
                            stock_item_name = item.name,
                            message = f"Essential {item.name} is low",
                            detail = "Time to restock — flagged as essential.",
                            related_date = None,
                        ))
                    else:
                        raw.append(AlertDto(
                            alert_id = stock_alert_key(item.id, "low_stock"),
                            kind = "low_stock",
                            severity = SEVERITY_LOW,
                            stock_item_id = item.id,
                            stock_item_name = item.name,
                            message = f"{item.name} is low",
                            detail = None,
                            related_date = None,
                        ))

        # ── Stocktake overdue ──────────────────────────────────────────
        # Single authority (R-003) — same resolver the runner queue uses,
        # so the bell and the runner never surface different sets. The
        # helper already applies mute + push (snooze) + engagement gate
        # + band resolution in one bulk pass.
        overdue_map = resolve_overdue_map(items, now)
        for item in items:
            info = overdue_map.get(item.id)
            if info is None:
                continue
            raw.append(AlertDto(
                alert_id = stock_alert_key(item.id, "stocktake_overdue"),
                kind = "stocktake_overdue",
                severity = SEVERITY_LOW,
                stock_item_id = item.id,
                stock_item_name = item.name,
                message = f"{item.name} needs a stocktake",
                detail = f"Overdue by {info.days} day(s).",
                related_date = None,
            ))

        # ── Forward-looking nudges (C-9.4) ─────────────────────────────
        # Not per-item, so they sit outside the loop. R-021 — `today` is
        # the household-tz boundary built once at the top of `handle()`.
        raw.extend(self._no_planned_meals_alerts(today))
        raw.extend(self._shopping_day_alerts(today))

        # ── Per-user overlay (C-9.1 interactions + C-9.2 preferences) ───
        # One bounded fetch each of this user's interactions + preferences,
        # then a Python-side filter — same shape as the suggestions flow.
        interactions: dict[str, AlertInteraction] = {}
        preferences: dict[str, AlertPreference] = {}
        if user_id is not None:
            interaction_rows: List[AlertInteraction] = self.repository.get(AlertInteraction).all(
                EntityField(AlertInteraction, AlertInteraction.Fields.USER_ID).eq(user_id)
            )
            interactions = {row.alert_key: row for row in interaction_rows}
            preference_rows: List[AlertPreference] = self.repository.get(AlertPreference).all(
                EntityField(AlertPreference, AlertPreference.Fields.USER_ID).eq(user_id)
            )
            preferences = {row.kind: row for row in preference_rows}

        active: List[AlertDto] = []
        snoozed: List[AlertDto] = []
        high = medium = low = 0
        actionable = fyi = 0

        for alert in raw:
            # a kind this user disabled contributes nothing to their
            # set, counts, or (later) channels.
            pref = preferences.get(alert.kind)
            if pref is not None and not pref.enabled:
                continue
            # Effective tier = this user's override, else the kind's default
            # (PROPOSAL_ALERTS §5). Drives the actionable/FYI count split.
            tier = (
                pref.tier_override
                if (pref is not None and pref.tier_override)
                else default_tier_for(alert.kind)
            )

            interaction = interactions.get(alert.alert_id)
            if interaction is not None and interaction.dismissed_at is not None:
                continue  # dismissed → hidden everywhere
            snooze_until = _active_snooze_until(interaction, now)
            read = interaction is not None and interaction.read_at is not None
            if snooze_until is not None:
                snoozed.append(replace(
                    alert, tier=tier, read=read, snoozed_until=snooze_until.isoformat()
                ))
                continue
            active.append(replace(alert, tier=tier, read=read, snoozed_until=None))
            # Severity counts feed the "X high · Y medium · Z low" caption; the
            # tier split feeds the badge (so a promoted low kind bumps it).
            if alert.severity == SEVERITY_HIGH:
                high += 1
            elif alert.severity == SEVERITY_MEDIUM:
                medium += 1
            else:
                low += 1
            if tier == TIER_ACTIONABLE:
                actionable += 1
            else:
                fyi += 1

        # Severity-first ordering so the panel scans top-down.
        def _sort_key(a: AlertDto):
            # Non-stock kinds (C-9.4) have no item name — fall back to the
            # message so the secondary sort stays total.
            label = a.stock_item_name or a.message
            return (_SEVERITY_ORDER.get(a.severity, 99), label.lower())

        active.sort(key=_sort_key)
        snoozed.sort(key=_sort_key)

        return AlertsDto(
            items=active,
            snoozed=snoozed,
            high_count=high,
            medium_count=medium,
            low_count=low,
            actionable_count=actionable,
            fyi_count=fyi,
            snoozed_count=len(snoozed),
        )

    def _no_planned_meals_alerts(self, today: date) -> List[AlertDto]:
        """One FYI nudge when *next* week has no meal-plan entries. The key is
        keyed on next week's ISO label so it clears the moment a meal lands in
        that week and re-fires for the following empty week."""
        # Next week = the seven days following this week's Sunday. weekday():
        # Mon=0 … Sun=6, so days to next Monday is 7 - weekday().
        next_monday = today + timedelta(days=7 - today.weekday())
        next_sunday = next_monday + timedelta(days=6)
        entries: List[MealPlanEntry] = self.repository.get(MealPlanEntry).all(
            EntityField(MealPlanEntry, MealPlanEntry.Fields.SCHEDULED_FOR)
            .between(next_monday, next_sunday)
        )
        if entries:
            return []
        return [AlertDto(
            alert_id = meal_alert_key(f"no_planned_meals:{_iso_week_label(next_monday)}"),
            kind = "no_planned_meals",
            severity = SEVERITY_LOW,
            message = "No meals planned for next week",
            detail = (
                f"Next week ({next_monday.strftime('%a %d %b')} – "
                f"{next_sunday.strftime('%a %d %b')}) has nothing on the plan yet."
            ),
            related_date = next_monday.isoformat(),
        )]

    def _shopping_day_alerts(self, today: date) -> List[AlertDto]:
        """One FYI nudge per not-yet-done list whose planned shop date is
        within reach. Upcoming window is the next `SHOPPING_DAY_WINDOW_DAYS`
        (today inclusive); overdue (planned date already passed, list still
        not done) also alerts so the bell mirrors the in-page banner's
        "today / tomorrow / overdue" tinting (FU-074). Reads the existing
        `planned_shop_date` (P6-01) — no schema. Clears when the list flips
        to done. One alert per list, keyed by `list_alert_key` — the same
        key is reused whether the list is upcoming or overdue, so user
        snooze/dismiss decisions persist as the date rolls past."""
        horizon = today + timedelta(days=SHOPPING_DAY_WINDOW_DAYS)
        lists: List[ShoppingList] = self.repository.get(ShoppingList).all(
            EntityField(ShoppingList, ShoppingList.Fields.PLANNED_SHOP_DATE)
            .lte(horizon)
            & EntityField(ShoppingList, ShoppingList.Fields.STATUS)
            .ne(SHOPPING_LIST_STATUS_DONE)
        )
        out: List[AlertDto] = []
        for lst in lists:
            days = (lst.planned_shop_date - today).days
            if days < 0:
                # Overdue: planned shop day already passed and the list still
                # isn't done. Bump severity so it sorts above plain upcoming
                # nudges; tier stays FYI (per kind default), so the bell badge
                # isn't inflated by what's still a soft nudge.
                overdue = -days
                when = "yesterday" if overdue == 1 else f"{overdue} days ago"
                message = f"Shopping day was {when}: {lst.display_name}"
                detail = "Mark it done or move the date."
                severity = SEVERITY_MEDIUM
            else:
                when = (
                    "today" if days == 0
                    else "tomorrow" if days == 1
                    else f"in {days} days"
                )
                message = f"Shopping day {when}: {lst.display_name}"
                detail = "Open the list to get ready."
                severity = SEVERITY_LOW
            out.append(AlertDto(
                alert_id = list_alert_key(lst.id, "shopping_day"),
                kind = "shopping_day",
                severity = severity,
                message = message,
                detail = detail,
                target_id = str(lst.id),
                related_date = lst.planned_shop_date.isoformat(),
            ))
        return out


@ALERT_ROUTER.route("", methods=["GET"])
def get_alerts():
    _Logger = logging.getLogger(__name__)
    _Alerts = GetAlertsHandler(SqlAlchemyRepository()).handle(_current_user_id())
    _Logger.debug(
        "Alerts: %d actionable, %d fyi, %d snoozed",
        _Alerts.actionable_count, _Alerts.fyi_count, _Alerts.snoozed_count,
    )
    return ok(_Alerts)
