"""GET /api/alerts — items that need the user's attention right now.

All signals are derived from existing schema (expiry_date, stock_level,
stock_level_last_updated, days_until_stocktake_alert, is_flagged), so the
alert *conditions* are never stored — they're recomputed every request and
so always reflect current pantry state. The same reasoning engine used by
the locations heatmap powers this list — that consistency is intentional:
if the heatmap says a zone is red, the bell icon shows you which items
inside that zone are why.

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
from datetime import date, datetime, timezone
from typing import List
from uuid import UUID

from flask import session

from dora_api.domain.entities.alert_interaction import AlertInteraction
from dora_api.domain.entities.alert_preference import AlertPreference
from dora_api.domain.entities.app_setting import AppSetting
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import (effective_expiring_soon_window,
                                          is_low_stock, is_out_of_stock)
from dora_api.features.alerts.alert_key import stock_alert_key
from dora_api.features.alerts.alert_kinds import (TIER_ACTIONABLE,
                                                  default_tier_for)
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Severities are an ordinal scale — the UI sorts high first, then medium,
# then low. The bell *badge* counts the actionable tier (high+medium); low
# is FYI and shown but not counted into the badge (PROPOSAL_ALERTS §3.4).
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

_SEVERITY_ORDER = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}


@dataclass(frozen=True, slots=True)
class AlertDto:
    # Stable scoped key `<scope>:<id>:<kind>` (alert_key) — the frontend
    # treats it as an opaque id and posts it back to the snooze/read/dismiss
    # endpoints. Named `alert_id` for frontend continuity; its *value* is the
    # generalised key (alert_key.py).
    alert_id: str
    kind: str  # 'expired' | 'expiring_soon' | 'out_of_stock' | 'low_stock' | 'stocktake_overdue' | 'essential_low'
    severity: str
    stock_item_id: UUID
    stock_item_name: str
    message: str
    detail: str | None
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
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, user_id: UUID | None = None) -> AlertsDto:
        items: List[StockItem] = (
            self.repository.get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .all()
        )
        today = date.today()
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

            # ── Stocktake overdue ──────────────────────────────────────
            if (
                item.stocktake_alerts_are_enabled
                and item.stock_level_last_updated is not None
                and item.days_until_stocktake_alert is not None
            ):
                last = item.stock_level_last_updated
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                elapsed_days = (now - last).days
                if elapsed_days > item.days_until_stocktake_alert:
                    overdue_by = elapsed_days - item.days_until_stocktake_alert
                    raw.append(AlertDto(
                        alert_id = stock_alert_key(item.id, "stocktake_overdue"),
                        kind = "stocktake_overdue",
                        severity = SEVERITY_LOW,
                        stock_item_id = item.id,
                        stock_item_name = item.name,
                        message = f"{item.name} needs a stocktake",
                        detail = f"Overdue by {overdue_by} day(s).",
                        related_date = None,
                    ))

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
            # C-9.2 — a kind this user disabled contributes nothing to their
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
            return (_SEVERITY_ORDER.get(a.severity, 99), a.stock_item_name.lower())

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


@ALERT_ROUTER.route("", methods=["GET"])
def get_alerts():
    _Logger = logging.getLogger(__name__)
    _Alerts = get_container().inject(GetAlertsHandler).handle(_current_user_id())
    _Logger.debug(
        "Alerts: %d actionable, %d fyi, %d snoozed",
        _Alerts.actionable_count, _Alerts.fyi_count, _Alerts.snoozed_count,
    )
    return ok(_Alerts)
