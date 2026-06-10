"""GET /api/alerts — items that need the user's attention right now.

All signals are derived from existing schema (expiry_date, stock_level,
stock_level_last_updated, days_until_stocktake_alert, is_flagged), so no
new tables. The same reasoning engine used by the locations heatmap powers
this list — that consistency is intentional: if the heatmap says a zone is
red, the bell icon shows you which items inside that zone are why.

Severity is one of "high" / "medium" / "low" so the UI can sort/colour
without having to recompute the weight.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List
from uuid import UUID

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import (EXPIRING_SOON_WINDOW_DAYS,
                                          is_low_stock, is_out_of_stock)
from dora_api.features.routers import ALERT_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Severities are an ordinal scale — the UI sorts high first, then medium,
# then low; counts on the bell badge use high+medium so low-severity
# noise doesn't drive the number up.
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


@dataclass(frozen=True, slots=True)
class AlertDto:
    # Composite ID so the frontend can dedupe / dismiss with a stable key.
    # Format: `<stock_item_id>:<kind>` — multiple alerts per item are
    # possible (expired AND flagged AND low stock, say).
    alert_id: str
    kind: str  # 'expired' | 'expiring_soon' | 'out_of_stock' | 'low_stock' | 'stocktake_overdue' | 'essential_low'
    severity: str
    stock_item_id: UUID
    stock_item_name: str
    message: str
    detail: str | None
    # ISO date string (if relevant — e.g. expiry alerts include the date).
    related_date: str | None = None


@dataclass(frozen=True, slots=True)
class AlertsDto:
    items: List[AlertDto] = field(default_factory=list)
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class GetAlertsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> AlertsDto:
        items: List[StockItem] = (
            self.repository.get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .all()
        )
        today = date.today()
        now = datetime.now(timezone.utc)

        alerts: List[AlertDto] = []
        high = medium = low = 0

        def push(alert: AlertDto):
            nonlocal high, medium, low
            alerts.append(alert)
            if alert.severity == SEVERITY_HIGH:
                high += 1
            elif alert.severity == SEVERITY_MEDIUM:
                medium += 1
            else:
                low += 1

        for item in items:
            # ── Expiry ─────────────────────────────────────────────────
            if item.expiry_date is not None:
                days_remaining = (item.expiry_date - today).days
                if days_remaining < 0:
                    push(AlertDto(
                        alert_id = f"{item.id}:expired",
                        kind = "expired",
                        severity = SEVERITY_HIGH,
                        stock_item_id = item.id,
                        stock_item_name = item.name,
                        message = f"{item.name} has expired",
                        detail = f"Expired {abs(days_remaining)} day(s) ago.",
                        related_date = item.expiry_date.isoformat(),
                    ))
                elif days_remaining <= EXPIRING_SOON_WINDOW_DAYS:
                    push(AlertDto(
                        alert_id = f"{item.id}:expiring_soon",
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
                        push(AlertDto(
                            alert_id = f"{item.id}:essential_out",
                            kind = "essential_low",
                            severity = SEVERITY_HIGH,
                            stock_item_id = item.id,
                            stock_item_name = item.name,
                            message = f"Essential {item.name} is out of stock",
                            detail = "Add it to your shopping list — you've flagged this as essential.",
                            related_date = None,
                        ))
                    else:
                        push(AlertDto(
                            alert_id = f"{item.id}:out_of_stock",
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
                        push(AlertDto(
                            alert_id = f"{item.id}:essential_low",
                            kind = "essential_low",
                            severity = SEVERITY_HIGH,
                            stock_item_id = item.id,
                            stock_item_name = item.name,
                            message = f"Essential {item.name} is low",
                            detail = "Time to restock — flagged as essential.",
                            related_date = None,
                        ))
                    else:
                        push(AlertDto(
                            alert_id = f"{item.id}:low_stock",
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
                    push(AlertDto(
                        alert_id = f"{item.id}:stocktake_overdue",
                        kind = "stocktake_overdue",
                        severity = SEVERITY_LOW,
                        stock_item_id = item.id,
                        stock_item_name = item.name,
                        message = f"{item.name} needs a stocktake",
                        detail = f"Overdue by {overdue_by} day(s).",
                        related_date = None,
                    ))

        # Severity-first ordering so the panel scans top-down.
        severity_order = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}
        alerts.sort(key=lambda a: (severity_order.get(a.severity, 99), a.stock_item_name.lower()))

        return AlertsDto(items=alerts, high_count=high, medium_count=medium, low_count=low)


@ALERT_ROUTER.route("", methods=["GET"])
def get_alerts():
    _Logger = logging.getLogger(__name__)
    _Alerts = get_container().inject(GetAlertsHandler).handle()
    _Logger.debug(
        "Alerts: %d high, %d medium, %d low",
        _Alerts.high_count, _Alerts.medium_count, _Alerts.low_count,
    )
    return ok(_Alerts)
