"""Heatmap / attention scoring.

Per-item and rolled-up per-location scoring used by the locations view.

Per-item attention is calculated from the item's own state. Per-location
attention is a count-weighted score across all descendant items, so a single
expired item doesn't paint a whole zone red — but many small issues add up.

Score is clamped to 100. The colour band is decided client-side; this module
returns the score and a structured `reasons` breakdown so the UI can render
"2 expired, 4 low stock, 1 flagged".
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Iterable

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import is_low_stock, is_out_of_stock


# Tunable weights. Tweak here, not in callers.
WEIGHT_EXPIRED = 25
WEIGHT_EXPIRING_SOON = 6
WEIGHT_OUT_OF_STOCK = 15
WEIGHT_LOW_STOCK = 8
WEIGHT_FLAGGED = 5
WEIGHT_STOCKTAKE_OVERDUE = 5

EXPIRING_SOON_WINDOW_DAYS = 7


@dataclass
class AttentionReasons:
    expired: int = 0
    expiring_soon: int = 0
    out_of_stock: int = 0
    low_stock: int = 0
    flagged: int = 0
    stocktake_overdue: int = 0

    def merge(self, other: "AttentionReasons") -> "AttentionReasons":
        return AttentionReasons(
            expired = self.expired + other.expired,
            expiring_soon = self.expiring_soon + other.expiring_soon,
            out_of_stock = self.out_of_stock + other.out_of_stock,
            low_stock = self.low_stock + other.low_stock,
            flagged = self.flagged + other.flagged,
            stocktake_overdue = self.stocktake_overdue + other.stocktake_overdue,
        )

    def score(self) -> int:
        total = (
            self.expired * WEIGHT_EXPIRED
            + self.expiring_soon * WEIGHT_EXPIRING_SOON
            + self.out_of_stock * WEIGHT_OUT_OF_STOCK
            + self.low_stock * WEIGHT_LOW_STOCK
            + self.flagged * WEIGHT_FLAGGED
            + self.stocktake_overdue * WEIGHT_STOCKTAKE_OVERDUE
        )
        return min(total, 100)

    def primary_label(self) -> str | None:
        """Short, human-readable summary of the worst-offending reason.

        Used in card subtitles where there isn't room to list every reason.
        """
        if self.expired:
            return f"{self.expired} expired"
        if self.out_of_stock:
            return f"{self.out_of_stock} out of stock"
        if self.low_stock:
            return f"{self.low_stock} low stock"
        if self.expiring_soon:
            return f"{self.expiring_soon} expiring soon"
        if self.stocktake_overdue:
            return f"{self.stocktake_overdue} stocktake overdue"
        if self.flagged:
            return f"{self.flagged} flagged"
        return None


def reasons_for_item(item: StockItem, today: date | None = None) -> AttentionReasons:
    today = today or date.today()
    r = AttentionReasons()

    if item.expiry_date is not None:
        if item.expiry_date < today:
            r.expired = 1
        elif (item.expiry_date - today).days <= EXPIRING_SOON_WINDOW_DAYS:
            r.expiring_soon = 1

    if item.stock_level is not None:
        if is_out_of_stock(item.stock_level):
            r.out_of_stock = 1
        elif is_low_stock(item.stock_level):
            r.low_stock = 1

    if item.is_flagged:
        r.flagged = 1

    if (
        item.stocktake_alerts_are_enabled
        and item.stock_level_last_updated is not None
        and item.days_until_stocktake_alert is not None
    ):
        last = item.stock_level_last_updated
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed_days = (datetime.now(timezone.utc) - last).days
        if elapsed_days > item.days_until_stocktake_alert:
            r.stocktake_overdue = 1

    return r


def reasons_for_items(items: Iterable[StockItem], today: date | None = None) -> AttentionReasons:
    total = AttentionReasons()
    for item in items:
        total = total.merge(reasons_for_item(item, today=today))
    return total
