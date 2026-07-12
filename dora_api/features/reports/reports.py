"""N6 — Reports / Analytics endpoints.

All six reports live in one module because they share assumptions (range
parsing, archived-list filtering, the "estimate not accounting" caveat on
prices) and because keeping them together means one place to revisit when
the schema shifts. The frontend hits each independently from /reports.

Endpoints:

  GET /api/reports/stock-value-over-time?range=30d|90d|1y
      Per-day stock value estimate.

  GET /api/reports/spend-by-store?range=...
      Per-store spend on archived lists.

  GET /api/reports/most-bought-items?range=...&limit=10
      Top stock items by archived-list appearances.

  GET /api/reports/keeps-running-out?limit=10
      Items most often "Out of Stock" at the moment they hit a list.

  GET /api/reports/price-trends?product_ids=<csv>&range=...
      Per-product unit price series; up to 5 products at once.

  GET /api/reports/savings-captured?range=...
      Aggregated picked-vs-RRP savings across archived lists.

  GET /api/reports/price-drops?limit=N
      Tracked products whose current offer is at a genuine new all-time low
      vs their historic offers.

Conventions:
- `range=all` is accepted everywhere a range is and means "no lower bound".
- Prices use the moment-of-pick snapshot pair on ShoppingListLine
  (picked_offer_price, list_price_at_pick) added in migration c6e9f4a82d15.
  Lines without a snapshot (legacy, or never ticked) are skipped, never
  fudged with current prices.
- Stock value is intentionally rough — "estimate, not accounting" — and
  noted in the response so the frontend can render the caveat.
"""
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from uuid import UUID

from flask import request
from sqlalchemy import func, or_, select

from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import \
    ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DONE,
                                                    ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.cook_event import CookEvent
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_level_change import StockLevelChange
from dora_api.domain.entities.stock_item_price_observation import StockItemPriceObservation
from dora_api.domain.stock_status import (StockStatus, get_stock_item_unit_cost_at,
                                          level_for_status)
from dora_api.features.routers import REPORTS_ROUTER
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


_Logger = logging.getLogger(__name__)


# ───── Range helpers ──────────────────────────────────────────────────────

# Range tokens accepted on every endpoint with a `range=` query. Mapped to
# a lower bound (UTC) or None for "all time". `1y`/`2y`/`5y` are flat
# 365-day multiples rather than calendar years so the chart axis is stable.
# 2y/5y are what the Memory section reads for "dairy up 8% over 2 years".
_RANGE_DAYS = {
    "30d": 30,
    "90d": 90,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
}


def _parse_range(raw: str | None) -> datetime | None:
    """Returns the lower-bound datetime for filtering, or None for 'all'.
    Defaults to 30 days when the param is missing or unrecognised — that's
    the most useful default for the page's initial render.
    """
    token = (raw or "30d").strip().lower()
    if token == "all":
        return None
    days = _RANGE_DAYS.get(token, 30)
    return datetime.now(timezone.utc) - timedelta(days=days)


def _range_days(raw: str | None) -> int | None:
    """Number of days the range spans, or None for 'all'. Used by
    endpoints that need to compute a same-length prior window (YoY)."""
    token = (raw or "30d").strip().lower()
    if token == "all":
        return None
    return _RANGE_DAYS.get(token, 30)


def _bucket_size_days(since: datetime | None) -> int:
    """Pick a day-bucket size that keeps the time series readable.
    30d → daily, 90d → daily, 1y → weekly. 2y/5y/all-time → monthly.
    """
    if since is None:
        return 30
    span = (datetime.now(timezone.utc) - since).days
    if span > 500:
        return 30    # monthly-ish for 2y/5y/all
    if span > 120:
        return 7     # weekly for 1y
    return 1         # daily for 30d/90d


# ───── 1. Stock value over time ───────────────────────────────────────────

@dataclass(slots=True)
class StockValuePoint:
    date: str
    value: float


class StockValueOverTimeHandler:
    """Estimate of total pantry value over time.

    Per-bucket formula: sum over stock items of
        (stock_level.sequence as-of bucket date) *
        (cheapest linked-product unit price as-of bucket date)

    Level rank uses StockLevelChange history; price uses ProductOffer +
    ProductHistoricOffer combined and filtered to "most recent ≤ bucket"
    per linked product, then the minimum across the item's linked products.
    Items with no linked-product price as-of a bucket fall back to the item's
    own price observations (FU-216 — the everyday substrate); items with
    neither a priced linked product nor an observation contribute zero.

    Cost: O(buckets × items × linked-products-per-item) in Python after one
    bulk load of changes and offers, which is fine for the pantry sizes this
    app targets.
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, since: datetime | None) -> List[StockValuePoint]:
        session = self.repository.session
        items: List[StockItem] = self.repository.get(StockItem).all()
        if not items:
            return []

        # Pre-load level history for every item, sorted ascending. We'll walk
        # it bucket-by-bucket with a per-item cursor.
        level_rows = session.execute(
            select(
                StockLevelChange.stock_item_id,
                StockLevelChange.changed_at,
                StockLevelChange.stock_level_id,
            ).order_by(StockLevelChange.changed_at.asc())
        ).all()
        changes_by_item: Dict[UUID, list] = {}
        for stock_item_id, changed_at, level_id in level_rows:
            changes_by_item.setdefault(stock_item_id, []).append((changed_at, level_id))

        # Level rank lookup; items missing from this map (e.g. a level
        # deleted out from under us) contribute zero rank.
        levels = self.repository.get(StockLevel).all()
        rank_by_level: Dict[UUID, int] = {l.id: int(l.sequence) for l in levels}
        rank_by_current_level: Dict[UUID, int] = {
            i.id: int(i.stock_level.sequence) if i.stock_level else 0
            for i in items
        }

        # Linked products per item (m2m) → most-recent price history. Pull
        # current + historic offers across every linked product, merge per
        # product, sort ascending.
        product_ids_by_item: Dict[UUID, list[UUID]] = {
            i.id: [p.id for p in (i.products or [])] for i in items
        }
        all_product_ids = {pid for ids in product_ids_by_item.values() for pid in ids}
        prices_by_product: Dict[UUID, list] = {pid: [] for pid in all_product_ids}
        if all_product_ids:
            current_rows = session.execute(
                select(
                    ProductOffer._product_id,  # noqa: SLF001 — mapped col alias
                    ProductOffer.offered_on,
                    ProductOffer.price_now,
                ).where(ProductOffer._product_id.in_(all_product_ids))
            ).all()
            historic_rows = session.execute(
                select(
                    ProductHistoricOffer._product_id,  # noqa: SLF001
                    ProductHistoricOffer.offered_on,
                    ProductHistoricOffer.price_now,
                ).where(ProductHistoricOffer._product_id.in_(all_product_ids))
            ).all()
            for pid, offered_on, price_now in list(current_rows) + list(historic_rows):
                if offered_on is None or price_now is None:
                    continue
                prices_by_product.setdefault(pid, []).append((offered_on, float(price_now)))
            for pid in prices_by_product:
                prices_by_product[pid].sort(key=lambda r: r[0])

        # price observations per item, for the fallback when an item
        # has no linked-product price as-of a bucket (PROPOSAL §3.2).
        observations_by_item: Dict[UUID, list] = {}
        _ItemIds = [i.id for i in items]
        if _ItemIds:
            for _Obs in self.repository.get(StockItemPriceObservation).all(
                EntityField(StockItemPriceObservation, "stock_item_id").in_(_ItemIds)
            ):
                # SQLite drops tzinfo on DateTime(timezone=True); coerce so the
                # observed_at compares cleanly against the tz-aware cursor in
                # get_stock_item_unit_cost_at.
                if _Obs.observed_at is not None and _Obs.observed_at.tzinfo is None:
                    _Obs.observed_at = _Obs.observed_at.replace(tzinfo=timezone.utc)
                observations_by_item.setdefault(_Obs.stock_item_id, []).append(_Obs)

        # Bucket boundaries.
        now = datetime.now(timezone.utc)
        bucket_days = _bucket_size_days(since)
        start = since or _as_utc(_earliest_change(level_rows)) or (now - timedelta(days=90))
        if start > now:
            start = now - timedelta(days=30)
        # Snap start to a midnight UTC boundary so points line up across reloads.
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)

        points: List[StockValuePoint] = []
        cursor = start
        while cursor <= now:
            total = 0.0
            for item in items:
                # Resolve as-of-cursor level. Falls back to the item's
                # current level when no change row precedes the bucket
                # (the change log only logs *transitions*, so the very
                # first level for an item is implicit).
                rank = _rank_as_of(
                    item.id,
                    cursor,
                    changes_by_item,
                    rank_by_level,
                    rank_by_current_level,
                )
                if rank <= 0:
                    continue
                linked = product_ids_by_item.get(item.id) or []
                price = _cheapest_as_of(linked, cursor, prices_by_product) if linked else None
                if price is None:
                    # fall back to the item's own price observations
                    # (everyday substrate; PROPOSAL_PRODUCTS_AS_OVERLAY §3.2)
                    # when there's no linked-product price as-of this bucket.
                    price = get_stock_item_unit_cost_at(
                        observations_by_item.get(item.id, []), when=cursor,
                    )
                if price is None:
                    continue
                total += rank * price
            points.append(StockValuePoint(date=cursor.date().isoformat(), value=round(total, 2)))
            cursor = cursor + timedelta(days=bucket_days)

        return points


def _earliest_change(level_rows) -> datetime | None:
    if not level_rows:
        return None
    return level_rows[0][1]


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _rank_as_of(
    item_id: UUID,
    cursor: datetime,
    changes_by_item: Dict[UUID, list],
    rank_by_level: Dict[UUID, int],
    rank_by_current_level: Dict[UUID, int],
) -> int:
    history = changes_by_item.get(item_id)
    if not history:
        return rank_by_current_level.get(item_id, 0)
    last_level_id = None
    for changed_at, level_id in history:
        changed_at = _as_utc(changed_at)
        if changed_at and changed_at > cursor:
            break
        last_level_id = level_id
    if last_level_id is None:
        return rank_by_current_level.get(item_id, 0)
    return rank_by_level.get(last_level_id, 0)


def _price_as_of(
    product_id: UUID,
    cursor: datetime,
    prices_by_product: Dict[UUID, list],
) -> float | None:
    series = prices_by_product.get(product_id)
    if not series:
        return None
    last_price = None
    for offered_on, price in series:
        offered_on = _as_utc(offered_on)
        if offered_on > cursor:
            break
        last_price = price
    return last_price


def _cheapest_as_of(
    product_ids: list[UUID],
    cursor: datetime,
    prices_by_product: Dict[UUID, list],
) -> float | None:
    cheapest = None
    for pid in product_ids:
        price = _price_as_of(pid, cursor, prices_by_product)
        if price is None:
            continue
        if cheapest is None or price < cheapest:
            cheapest = price
    return cheapest


@REPORTS_ROUTER.route("/stock-value-over-time", methods=["GET"])
def stock_value_over_time():
    _Since = _parse_range(request.args.get("range"))
    _Points = StockValueOverTimeHandler(SqlAlchemyRepository()).handle(_Since)
    return ok({
        "range": request.args.get("range", "30d"),
        "estimate_note": (
            "Estimate: level rank × cheapest most-recent linked-product price. "
            "Not accounting."
        ),
        "points": [asdict(p) for p in _Points],
    })


# ───── 2. Spend by store ──────────────────────────────────────────────────

@dataclass(slots=True)
class StoreSpendRow:
    store_id: UUID | None
    store: str
    spend: float
    list_count: int


class SpendByStoreHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, since: datetime | None) -> List[StoreSpendRow]:
        session = self.repository.session

        # Only archived (completed) lists within the window contribute.
        list_query = select(ShoppingList.id, ShoppingList.completed_at).where(
            ShoppingList.status == SHOPPING_LIST_STATUS_DONE
        )
        if since is not None:
            list_query = list_query.where(ShoppingList.completed_at >= since)
        list_rows = session.execute(list_query).all()
        list_ids = [row[0] for row in list_rows]
        if not list_ids:
            return []

        # Ticked lines with *any* captured price — the user's till-receipt
        # override (actual_unit_price) wins over the offer snapshot
        # (picked_offer_price). Matches the budget / waste / assistant /
        # suggestions ladder via `line_paid_unit_price` (R-003 chokepoint in
        # `shopping_lists/_line_price.py`); FU-229 carve-out — this handler
        # works on column-projected rows rather than entity objects, so the
        # ladder is expressed here as `actual if actual is not None else picked`
        # instead of calling the helper. Lines with neither price stay
        # silently skipped — they're not "spend". `selected_product_id IS
        # NOT NULL` stays because store grouping needs a product.
        line_rows = session.execute(
            select(
                ShoppingListLine.shopping_list_id,
                ShoppingListLine.selected_product_id,
                ShoppingListLine.quantity,
                ShoppingListLine.picked_offer_price,
                ShoppingListLine.actual_unit_price,
            ).where(
                ShoppingListLine.shopping_list_id.in_(list_ids),
                ShoppingListLine.is_ticked == True,  # noqa: E712
                or_(
                    ShoppingListLine.picked_offer_price.isnot(None),
                    ShoppingListLine.actual_unit_price.isnot(None),
                ),
                ShoppingListLine.selected_product_id.isnot(None),
            )
        ).all()
        if not line_rows:
            return []

        product_ids = {row[1] for row in line_rows if row[1]}
        products = self.repository.get(Product).include(Product.Fields.STORE).all(
            EntityField(Product, "id").in_(list(product_ids))
        )
        store_by_product: Dict[UUID, Store] = {
            p.id: p.store for p in products if p.store
        }

        spend_by_store: Dict[UUID | None, float] = {}
        lists_by_store: Dict[UUID | None, set] = {}
        names: Dict[UUID | None, str] = {}
        for list_id, product_id, quantity, picked, actual in line_rows:
            store = store_by_product.get(product_id)
            store_id = store.id if store else None
            unit_price = float(actual if actual is not None else picked)
            spend_by_store[store_id] = (
                spend_by_store.get(store_id, 0.0)
                + unit_price * float(quantity or 1)
            )
            lists_by_store.setdefault(store_id, set()).add(list_id)
            names[store_id] = store.name if store else "Unknown"

        out: List[StoreSpendRow] = [
            StoreSpendRow(
                store_id=store_id,
                store=names[store_id],
                spend=round(spend, 2),
                list_count=len(lists_by_store.get(store_id, set())),
            )
            for store_id, spend in spend_by_store.items()
        ]
        out.sort(key=lambda r: (-r.spend, r.store.lower()))
        return out


@REPORTS_ROUTER.route("/spend-by-store", methods=["GET"])
def spend_by_store():
    _Since = _parse_range(request.args.get("range"))
    _Rows = SpendByStoreHandler(SqlAlchemyRepository()).handle(_Since)
    return ok({
        "range": request.args.get("range", "30d"),
        "rows": [asdict(r) for r in _Rows],
    })


# ───── 3. Most-bought items ───────────────────────────────────────────────

@dataclass(slots=True)
class MostBoughtRow:
    stock_item_id: UUID
    name: str
    appearances: int


class MostBoughtItemsHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, since: datetime | None, limit: int) -> List[MostBoughtRow]:
        session = self.repository.session

        list_query = select(ShoppingList.id).where(
            ShoppingList.status == SHOPPING_LIST_STATUS_DONE
        )
        if since is not None:
            list_query = list_query.where(ShoppingList.completed_at >= since)
        list_ids = [row[0] for row in session.execute(list_query).all()]
        if not list_ids:
            return []

        # Distinct-(list, item) count, so the same item appearing across
        # five lists scores 5, not 5 × however many times it was edited.
        count_rows = session.execute(
            select(
                ShoppingListLine.stock_item_id,
                func.count(func.distinct(ShoppingListLine.shopping_list_id)),
            ).where(ShoppingListLine.shopping_list_id.in_(list_ids))
            .group_by(ShoppingListLine.stock_item_id)
        ).all()
        if not count_rows:
            return []

        counts: Dict[UUID, int] = {row[0]: int(row[1]) for row in count_rows}
        items = self.repository.get(StockItem).all(
            EntityField(StockItem, "id").in_(list(counts.keys()))
        )
        rows = [
            MostBoughtRow(
                stock_item_id=item.id,
                name=item.name,
                appearances=counts.get(item.id, 0),
            )
            for item in items
        ]
        rows.sort(key=lambda r: (-r.appearances, r.name.lower()))
        return rows[:limit]


@REPORTS_ROUTER.route("/most-bought-items", methods=["GET"])
def most_bought_items():
    _Since = _parse_range(request.args.get("range"))
    try:
        _Limit = max(1, min(int(request.args.get("limit", "10")), 50))
    except (TypeError, ValueError):
        _Limit = 10
    _Rows = MostBoughtItemsHandler(SqlAlchemyRepository()).handle(_Since, _Limit)
    return ok({
        "range": request.args.get("range", "30d"),
        "rows": [asdict(r) for r in _Rows],
    })


# ───── 4. Keeps running out ───────────────────────────────────────────────

@dataclass(slots=True)
class KeepsRunningOutRow:
    stock_item_id: UUID
    name: str
    times_out_when_added: int


class KeepsRunningOutHandler:
    """Stock items most often at 'Out of Stock' at the moment they were
    added to a list. Walks the StockLevelChange history per item to
    resolve "what level was this when added_at happened", and tallies the
    out-of-stock occurrences.

    Lines without an `added_at` (legacy rows from before X5) are skipped
    rather than guessed.
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, limit: int) -> List[KeepsRunningOutRow]:
        session = self.repository.session

        out_level = level_for_status(
            self.repository.get(StockLevel).all(), StockStatus.OUT_OF_STOCK
        )
        if out_level is None:
            return []

        # Every (item, added_at) pair across history. We don't filter by
        # archived; "added when out" is the signal we want even on lists
        # the user never finished.
        add_rows = session.execute(
            select(
                ShoppingListLine.stock_item_id,
                ShoppingListLine.added_at,
            ).where(ShoppingListLine.added_at.isnot(None))
        ).all()
        if not add_rows:
            return []

        # Group by item.
        adds_by_item: Dict[UUID, list] = {}
        for stock_item_id, added_at in add_rows:
            adds_by_item.setdefault(stock_item_id, []).append(added_at)

        # Pull level history for those items, ordered asc.
        level_rows = session.execute(
            select(
                StockLevelChange.stock_item_id,
                StockLevelChange.changed_at,
                StockLevelChange.stock_level_id,
            ).where(StockLevelChange.stock_item_id.in_(list(adds_by_item.keys())))
            .order_by(StockLevelChange.changed_at.asc())
        ).all()
        changes_by_item: Dict[UUID, list] = {}
        for stock_item_id, changed_at, level_id in level_rows:
            changes_by_item.setdefault(stock_item_id, []).append((changed_at, level_id))

        # Items' current level, used as the fallback for adds that
        # predate any change-log entry. `.include(STOCK_LEVEL)` is
        # load-bearing (FU-527): `stock_level` is lazy="noload", so without
        # it the `_level_id_as_of` fallback read `item.stock_level` as None
        # and silently dropped every item with no change-log history from the
        # keeps-running-out tally.
        items = self.repository.get(StockItem).include(
            StockItem.Fields.STOCK_LEVEL
        ).all(
            EntityField(StockItem, "id").in_(list(adds_by_item.keys()))
        )
        items_by_id = {i.id: i for i in items}

        scores: Dict[UUID, int] = {}
        for item_id, timestamps in adds_by_item.items():
            for added_at in timestamps:
                level_id = _level_id_as_of(
                    item_id, added_at, changes_by_item, items_by_id
                )
                if level_id == out_level.id:
                    scores[item_id] = scores.get(item_id, 0) + 1

        out_rows: List[KeepsRunningOutRow] = []
        for item_id, count in scores.items():
            item = items_by_id.get(item_id)
            if item is None:
                continue
            out_rows.append(KeepsRunningOutRow(
                stock_item_id=item.id,
                name=item.name,
                times_out_when_added=count,
            ))
        out_rows.sort(key=lambda r: (-r.times_out_when_added, r.name.lower()))
        return out_rows[:limit]


def _level_id_as_of(
    item_id: UUID,
    when: datetime,
    changes_by_item: Dict[UUID, list],
    items_by_id: Dict[UUID, StockItem],
) -> UUID | None:
    history = changes_by_item.get(item_id, [])
    last_level_id = None
    for changed_at, level_id in history:
        if changed_at and changed_at > when:
            break
        last_level_id = level_id
    if last_level_id is not None:
        return last_level_id
    # Fallback: the item's *current* level (best we can do for adds that
    # happened before the change log started).
    item = items_by_id.get(item_id)
    return item.stock_level.id if item and item.stock_level else None


@REPORTS_ROUTER.route("/keeps-running-out", methods=["GET"])
def keeps_running_out():
    try:
        _Limit = max(1, min(int(request.args.get("limit", "10")), 50))
    except (TypeError, ValueError):
        _Limit = 10
    _Rows = KeepsRunningOutHandler(SqlAlchemyRepository()).handle(_Limit)
    return ok({"rows": [asdict(r) for r in _Rows]})


# ───── 5. Price trends ────────────────────────────────────────────────────

@dataclass(slots=True)
class PricePoint:
    date: str
    unit_price: float


@dataclass(slots=True)
class PriceTrendSeries:
    product_id: UUID
    name: str
    store: str
    points: List[PricePoint] = field(default_factory=list)


class PriceTrendsHandler:
    MAX_PRODUCTS = 5

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(
        self,
        product_ids: List[UUID],
        since: datetime | None,
    ) -> List[PriceTrendSeries]:
        if not product_ids:
            return []
        product_ids = product_ids[: self.MAX_PRODUCTS]
        session = self.repository.session

        products = self.repository.get(Product).include(Product.Fields.STORE).all(
            EntityField(Product, "id").in_(product_ids)
        )
        products_by_id = {p.id: p for p in products}

        # Current + historic offers for the requested products.
        current_rows = session.execute(
            select(
                ProductOffer._product_id,  # noqa: SLF001
                ProductOffer.offered_on,
                ProductOffer.price_now,
            ).where(ProductOffer._product_id.in_(product_ids))
        ).all()
        historic_rows = session.execute(
            select(
                ProductHistoricOffer._product_id,  # noqa: SLF001
                ProductHistoricOffer.offered_on,
                ProductHistoricOffer.price_now,
            ).where(ProductHistoricOffer._product_id.in_(product_ids))
        ).all()

        points_by_product: Dict[UUID, List[PricePoint]] = {}
        for pid, offered_on, price_now in list(current_rows) + list(historic_rows):
            if offered_on is None or price_now is None:
                continue
            if since is not None and offered_on < since:
                continue
            points_by_product.setdefault(pid, []).append(
                PricePoint(date=offered_on.date().isoformat(), unit_price=float(price_now))
            )

        out: List[PriceTrendSeries] = []
        for pid in product_ids:
            product = products_by_id.get(pid)
            if product is None:
                continue
            points = sorted(points_by_product.get(pid, []), key=lambda p: p.date)
            out.append(PriceTrendSeries(
                product_id=pid,
                name=product.name,
                store=product.store.name if product.store else "Unknown",
                points=points,
            ))
        return out


@REPORTS_ROUTER.route("/price-trends", methods=["GET"])
def price_trends():
    raw_ids = request.args.get("product_ids", "")
    product_ids: List[UUID] = []
    for chunk in raw_ids.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            product_ids.append(UUID(chunk))
        except ValueError:
            return bad_request(
                "Invalid product_ids",
                detail=f"'{chunk}' is not a UUID.",
            )

    _Since = _parse_range(request.args.get("range"))
    _Series = PriceTrendsHandler(SqlAlchemyRepository()).handle(product_ids, _Since)
    return ok({
        "range": request.args.get("range", "30d"),
        "series": [
            {
                "product_id": s.product_id,
                "name": s.name,
                "store": s.store,
                "points": [asdict(p) for p in s.points],
            }
            for s in _Series
        ],
    })


# ───── 6. Savings captured ────────────────────────────────────────────────

@dataclass(slots=True)
class SavingsListBreakdown:
    shopping_list_id: UUID
    name: str
    completed_at: datetime | None
    picked_total: float
    list_total: float
    savings: float


class SavingsCapturedHandler:
    """Aggregate savings = list_price_at_pick − picked_offer_price, per
    archived list with snapshot data. Lines without the RRP snapshot
    contribute zero to savings but still count toward picked_total
    (so the "total spent" matches spend-by-store)."""

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, since: datetime | None) -> dict:
        session = self.repository.session

        list_query = select(
            ShoppingList.id, ShoppingList.name, ShoppingList.completed_at
        ).where(ShoppingList.status == SHOPPING_LIST_STATUS_DONE)
        if since is not None:
            list_query = list_query.where(ShoppingList.completed_at >= since)
        list_rows = session.execute(list_query).all()
        list_ids = [row[0] for row in list_rows]
        if not list_ids:
            return {"total_savings": 0.0, "total_spent": 0.0, "lists": []}

        line_rows = session.execute(
            select(
                ShoppingListLine.shopping_list_id,
                ShoppingListLine.quantity,
                ShoppingListLine.picked_offer_price,
                ShoppingListLine.list_price_at_pick,
            ).where(
                ShoppingListLine.shopping_list_id.in_(list_ids),
                ShoppingListLine.is_ticked == True,  # noqa: E712
                ShoppingListLine.picked_offer_price.isnot(None),
            )
        ).all()

        picked_by_list: Dict[UUID, float] = {}
        list_total_by_list: Dict[UUID, float] = {}
        for lst_id, qty, picked, rrp in line_rows:
            q = float(qty or 1)
            picked_by_list[lst_id] = picked_by_list.get(lst_id, 0.0) + float(picked) * q
            # When the RRP snapshot is missing the list price falls back
            # to the picked price (so this line contributes 0 savings,
            # not negative).
            list_total_by_list[lst_id] = (
                list_total_by_list.get(lst_id, 0.0)
                + float(rrp if rrp is not None else picked) * q
            )

        breakdowns: List[SavingsListBreakdown] = []
        for list_id, name, completed_at in list_rows:
            picked_total = round(picked_by_list.get(list_id, 0.0), 2)
            list_total = round(list_total_by_list.get(list_id, 0.0), 2)
            if picked_total == 0.0:
                continue
            breakdowns.append(SavingsListBreakdown(
                shopping_list_id=list_id,
                name=name,
                completed_at=completed_at,
                picked_total=picked_total,
                list_total=list_total,
                savings=round(list_total - picked_total, 2),
            ))
        breakdowns.sort(
            key=lambda b: (b.completed_at or datetime.min.replace(tzinfo=timezone.utc)),
        )
        total_savings = round(sum(b.savings for b in breakdowns), 2)
        total_spent = round(sum(b.picked_total for b in breakdowns), 2)
        return {
            "total_savings": total_savings,
            "total_spent": total_spent,
            "lists": [
                {
                    "shopping_list_id": b.shopping_list_id,
                    "name": b.name,
                    "completed_at": b.completed_at,
                    "picked_total": b.picked_total,
                    "list_total": b.list_total,
                    "savings": b.savings,
                }
                for b in breakdowns
            ],
        }


@REPORTS_ROUTER.route("/savings-captured", methods=["GET"])
def savings_captured():
    _Since = _parse_range(request.args.get("range"))
    _Result = SavingsCapturedHandler(SqlAlchemyRepository()).handle(_Since)
    _Result["range"] = request.args.get("range", "30d")
    return ok(_Result)


# ───── 7. Price drops (new-low) ───────────────────────────────────────────

@dataclass(slots=True)
class PriceDropRow:
    product_id: UUID
    name: str
    store_id: UUID | None
    store_name: str
    has_image: bool
    price_now: float
    previous_low: float
    drop_amount: float
    drop_percent: int
    linked_stock_item_id: UUID | None
    linked_stock_item_name: str | None


class PriceDropsHandler:
    """Active products whose current offer is strictly below every prior
    historic price on record — Honesty (§2.4): the claim "new low" must be
    true, not "cheapest right now". Ranked by drop percent, sliced server-side
    (state-ownership §8.2)."""

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, limit: int) -> list[PriceDropRow]:
        products = (
            self.repository
            .get(Product)
            .include(Product.Fields.CURRENT_OFFER)
            .include(Product.Fields.STORE)
            .all()
        )
        active = [p for p in products if p.is_active and p.current_offer is not None]
        if not active:
            return []

        product_ids = [p.id for p in active]
        session = self.repository.session
        historic_rows = session.execute(
            select(
                ProductHistoricOffer._product_id,  # noqa: SLF001
                ProductHistoricOffer.price_now,
            ).where(ProductHistoricOffer._product_id.in_(product_ids))
        ).all()
        prev_low_by_product: Dict[UUID, float] = {}
        for pid, price_now in historic_rows:
            if price_now is None:
                continue
            price = float(price_now)
            existing = prev_low_by_product.get(pid)
            if existing is None or price < existing:
                prev_low_by_product[pid] = price

        rows: list[PriceDropRow] = []
        for product in active:
            prev_low = prev_low_by_product.get(product.id)
            # No prior history → the current price can't be a "new low" —
            # it's the only price we've seen. Skip.
            if prev_low is None or prev_low <= 0:
                continue
            current = float(product.current_offer.price_now)
            if current <= 0 or current >= prev_low:
                continue
            drop_amount = round(prev_low - current, 2)
            drop_percent = int(round((prev_low - current) / prev_low * 100))
            rows.append(PriceDropRow(
                product_id=product.id,
                name=product.name,
                store_id=product.store.id if product.store else None,
                store_name=product.store.name if product.store else "Unknown",
                has_image=False,
                price_now=current,
                previous_low=round(prev_low, 2),
                drop_amount=drop_amount,
                drop_percent=drop_percent,
                linked_stock_item_id=None,
                linked_stock_item_name=None,
            ))
        rows.sort(key=lambda r: (r.drop_percent, r.drop_amount), reverse=True)
        rows = rows[:limit]

        # Stamp has_image + linked_stock_item_* against the sliced set only,
        # so we never load the deferred image blob for the unsliced tail.
        # These live on Product; a lightweight direct SQL pass mirrors the
        # products list (get_products.stamp_has_image / stamp_linked_stock_items)
        # but on `PriceDropRow` shape (no shared DTO between the two).
        if rows:
            from dora_api.app import db  # local to avoid module-load cycles
            sliced_ids = [r.product_id for r in rows]
            product_table = db.metadata.tables["Product"]
            image_rows = session.execute(
                select(product_table.c.id, product_table.c.image.isnot(None))
                .where(product_table.c.id.in_(sliced_ids))
            ).all()
            has_image_by_id = {row[0]: bool(row[1]) for row in image_rows}
            assoc = db.metadata.tables["StockItemProduct"]
            link_rows = session.execute(
                select(assoc.c.product_id, assoc.c.stock_item_id)
                .where(assoc.c.product_id.in_(sliced_ids))
            ).all()
            product_to_stock: Dict[UUID, UUID] = {row[0]: row[1] for row in link_rows}
            stock_ids = list({sid for sid in product_to_stock.values()})
            name_by_stock: Dict[UUID, str] = {}
            if stock_ids:
                for item in self.repository.get(StockItem).all(
                    EntityField(StockItem, "id").in_(stock_ids)
                ):
                    name_by_stock[item.id] = item.name
            for row in rows:
                row.has_image = has_image_by_id.get(row.product_id, False)
                stock_id = product_to_stock.get(row.product_id)
                if stock_id is not None:
                    row.linked_stock_item_id = stock_id
                    row.linked_stock_item_name = name_by_stock.get(stock_id)
        return rows


@REPORTS_ROUTER.route("/price-drops", methods=["GET"])
def price_drops():
    try:
        _Limit = max(1, min(int(request.args.get("limit", "5")), 20))
    except (TypeError, ValueError):
        _Limit = 5
    _Rows = PriceDropsHandler(SqlAlchemyRepository()).handle(_Limit)
    return ok({"rows": [asdict(r) for r in _Rows]})


# ───── 8. Meals cooked over time (P8-09 memory) ───────────────────────────
# What was actually cooked in this window. Every CookEvent = one POST to
# /recipes/<id>/cook, so a Sunday batch-cook that fed the week leaves ONE
# row (not seven) — the count is honest about intent-events, not portions.
# `meals_cooked` on each event is the *portion count* the user entered on
# that cook, and the report sums those separately for "how many
# meals-worth" (rather than "how many cooking sessions").

@dataclass(slots=True)
class MealsCookedTopRow:
    recipe_id: UUID | None
    recipe_name: str
    cook_count: int      # number of CookEvent rows for this recipe
    meals_total: int     # sum of meals_cooked across those rows


@dataclass(slots=True)
class MealsCookedBucketPoint:
    date: str            # ISO date at the start of the bucket
    cook_count: int
    meals_total: int


class MealsCookedHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, since: datetime | None, limit: int) -> dict:
        session = self.repository.session

        query = select(
            CookEvent.recipe_id,
            CookEvent.recipe_name,
            CookEvent.meals_cooked,
            CookEvent.occurred_at,
        )
        if since is not None:
            query = query.where(CookEvent.occurred_at >= since)
        rows = session.execute(query).all()
        if not rows:
            return {
                "cook_count": 0,
                "meals_total": 0,
                "top_recipes": [],
                "timeline": [],
            }

        # Top-N recipes by cook_count (with meals_total as tiebreak signal
        # so a rice cooker cooked once feeding 8 doesn't outrank a nightly
        # curry). Group by recipe_id when non-null, else by the denorm name
        # so deleted-recipe events still land in a labelled bucket.
        by_key: dict[tuple, dict] = {}
        for row in rows:
            key = (row.recipe_id, row.recipe_name)
            bucket = by_key.setdefault(key, {
                "recipe_id": row.recipe_id,
                "recipe_name": row.recipe_name,
                "cook_count": 0,
                "meals_total": 0,
            })
            bucket["cook_count"] += 1
            bucket["meals_total"] += int(row.meals_cooked or 0)

        top = sorted(
            by_key.values(),
            key=lambda b: (-b["cook_count"], -b["meals_total"], b["recipe_name"].lower()),
        )[:limit]
        top_rows = [
            MealsCookedTopRow(
                recipe_id=b["recipe_id"],
                recipe_name=b["recipe_name"],
                cook_count=b["cook_count"],
                meals_total=b["meals_total"],
            )
            for b in top
        ]

        # Timeline — bucket by the shared _bucket_size_days helper so
        # 30d/90d get daily, 1y weekly, 2y+/all monthly. Deterministic
        # bucket edges relative to *now* (not the event stream) keep the
        # chart's x-axis stable across refreshes.
        bucket_days = _bucket_size_days(since)
        now = datetime.now(timezone.utc)
        # Strip tz for arithmetic against timestamps that may be tz-naive
        # (SQLite doesn't preserve tz; the mapper stores naive UTC).
        now_naive = now.replace(tzinfo=None)
        buckets: dict[str, dict[str, int]] = {}
        for row in rows:
            ts = row.occurred_at
            if ts is None:
                continue
            ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
            delta_days = (now_naive - ts_naive).days
            bucket_index = delta_days // bucket_days
            bucket_start = (now_naive - timedelta(days=(bucket_index + 1) * bucket_days - 1)).date()
            key = bucket_start.isoformat()
            b = buckets.setdefault(key, {"cook_count": 0, "meals_total": 0})
            b["cook_count"] += 1
            b["meals_total"] += int(row.meals_cooked or 0)

        timeline = [
            MealsCookedBucketPoint(
                date=date_key,
                cook_count=v["cook_count"],
                meals_total=v["meals_total"],
            )
            for date_key, v in sorted(buckets.items())
        ]

        return {
            "cook_count": len(rows),
            "meals_total": sum(int(r.meals_cooked or 0) for r in rows),
            "top_recipes": [asdict(r) for r in top_rows],
            "timeline": [asdict(p) for p in timeline],
        }


@REPORTS_ROUTER.route("/meals-cooked", methods=["GET"])
def meals_cooked():
    since = _parse_range(request.args.get("range"))
    try:
        limit = max(1, min(int(request.args.get("limit", "10")), 50))
    except (TypeError, ValueError):
        limit = 10
    payload = MealsCookedHandler(SqlAlchemyRepository()).handle(since, limit)
    return ok({
        "range": request.args.get("range", "30d"),
        **payload,
    })


# ───── 9. Spend by category (P8-09 memory) ────────────────────────────────
# Category = StockItem.stock_group (name). Aggregates paid unit price ×
# quantity on ticked lines of archived (done) lists in the range, joined
# through stock_item to its group. Lines with no stock_item, or whose stock
# item has no group, roll up into an "Uncategorised" bucket so nothing is
# silently dropped.

_UNCATEGORISED_LABEL = "Uncategorised"


@dataclass(slots=True)
class SpendByCategoryRow:
    category: str
    spent: float
    item_count: int  # distinct stock items contributing to this category
    share_pct: float


class SpendByCategoryHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, since: datetime | None) -> tuple[List[SpendByCategoryRow], float]:
        session = self.repository.session

        list_query = select(ShoppingList.id).where(
            ShoppingList.status == SHOPPING_LIST_STATUS_DONE
        )
        if since is not None:
            list_query = list_query.where(ShoppingList.completed_at >= since)
        list_ids = [row[0] for row in session.execute(list_query).all()]
        if not list_ids:
            return [], 0.0

        # Same actual→picked ladder as spend-by-store; same "silently skip
        # lines with no captured price" rule. This is genuine spend, so
        # unticked lines are excluded.
        line_rows = session.execute(
            select(
                ShoppingListLine.stock_item_id,
                ShoppingListLine.quantity,
                ShoppingListLine.picked_offer_price,
                ShoppingListLine.actual_unit_price,
            ).where(
                ShoppingListLine.shopping_list_id.in_(list_ids),
                ShoppingListLine.is_ticked == True,  # noqa: E712
                or_(
                    ShoppingListLine.picked_offer_price.isnot(None),
                    ShoppingListLine.actual_unit_price.isnot(None),
                ),
            )
        ).all()
        if not line_rows:
            return [], 0.0

        # Fetch every stock item referenced + its group name in one pass.
        # Duplicate keys collapse via dict comprehension.
        stock_ids = {r.stock_item_id for r in line_rows if r.stock_item_id is not None}
        group_by_item: dict[UUID, str] = {}
        if stock_ids:
            items = self.repository.get(StockItem).include("stock_group").all(
                EntityField(StockItem, "id").in_(list(stock_ids))
            )
            for item in items:
                group_name = (
                    item.stock_group.name.strip()
                    if item.stock_group is not None and item.stock_group.name
                    else _UNCATEGORISED_LABEL
                )
                group_by_item[item.id] = group_name

        by_category: dict[str, dict] = {}
        for row in line_rows:
            qty = row.quantity if row.quantity is not None else 1
            if qty <= 0:
                continue
            unit_price = (
                float(row.actual_unit_price)
                if row.actual_unit_price is not None
                else float(row.picked_offer_price)
            )
            spent = unit_price * qty
            category = (
                group_by_item.get(row.stock_item_id, _UNCATEGORISED_LABEL)
                if row.stock_item_id is not None
                else _UNCATEGORISED_LABEL
            )
            bucket = by_category.setdefault(
                category, {"spent": 0.0, "items": set()},
            )
            bucket["spent"] += spent
            if row.stock_item_id is not None:
                bucket["items"].add(row.stock_item_id)

        total = sum(b["spent"] for b in by_category.values())
        rows = [
            SpendByCategoryRow(
                category=category,
                spent=round(b["spent"], 2),
                item_count=len(b["items"]),
                share_pct=round((b["spent"] / total) * 100, 1) if total > 0 else 0.0,
            )
            for category, b in by_category.items()
        ]
        rows.sort(key=lambda r: (-r.spent, r.category.lower()))
        return rows, round(total, 2)


@REPORTS_ROUTER.route("/spend-by-category", methods=["GET"])
def spend_by_category():
    since = _parse_range(request.args.get("range"))
    rows, total = SpendByCategoryHandler(SqlAlchemyRepository()).handle(since)
    return ok({
        "range": request.args.get("range", "30d"),
        "total_spent": total,
        "rows": [asdict(r) for r in rows],
    })


# ───── 10. Spend year-over-year (P8-09 memory) ────────────────────────────
# Compares total spend + per-category spend between two same-length
# windows: the CURRENT window (range=N days ending now) and the PRIOR
# window immediately preceding it. E.g. range=1y → this year vs last
# year, category-by-category. Range=all is rejected — YoY needs a
# bounded window.

@dataclass(slots=True)
class SpendYoYCategoryRow:
    category: str
    current: float
    previous: float
    delta: float          # current - previous
    delta_pct: float | None  # None when previous == 0 (undefined)


class SpendYoYHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(
        self,
        current_since: datetime,
        previous_since: datetime,
        previous_until: datetime,
    ) -> dict:
        def _for_window(since: datetime, until: datetime | None) -> tuple[dict[str, float], float]:
            session = self.repository.session
            list_query = select(ShoppingList.id).where(
                ShoppingList.status == SHOPPING_LIST_STATUS_DONE,
                ShoppingList.completed_at >= since,
            )
            if until is not None:
                list_query = list_query.where(ShoppingList.completed_at < until)
            list_ids = [row[0] for row in session.execute(list_query).all()]
            if not list_ids:
                return {}, 0.0

            line_rows = session.execute(
                select(
                    ShoppingListLine.stock_item_id,
                    ShoppingListLine.quantity,
                    ShoppingListLine.picked_offer_price,
                    ShoppingListLine.actual_unit_price,
                ).where(
                    ShoppingListLine.shopping_list_id.in_(list_ids),
                    ShoppingListLine.is_ticked == True,  # noqa: E712
                    or_(
                        ShoppingListLine.picked_offer_price.isnot(None),
                        ShoppingListLine.actual_unit_price.isnot(None),
                    ),
                )
            ).all()
            if not line_rows:
                return {}, 0.0

            stock_ids = {r.stock_item_id for r in line_rows if r.stock_item_id is not None}
            group_by_item: dict[UUID, str] = {}
            if stock_ids:
                items = self.repository.get(StockItem).include("stock_group").all(
                    EntityField(StockItem, "id").in_(list(stock_ids))
                )
                for item in items:
                    group_by_item[item.id] = (
                        item.stock_group.name.strip()
                        if item.stock_group is not None and item.stock_group.name
                        else _UNCATEGORISED_LABEL
                    )

            by_category: dict[str, float] = {}
            for row in line_rows:
                qty = row.quantity if row.quantity is not None else 1
                if qty <= 0:
                    continue
                unit_price = (
                    float(row.actual_unit_price)
                    if row.actual_unit_price is not None
                    else float(row.picked_offer_price)
                )
                category = (
                    group_by_item.get(row.stock_item_id, _UNCATEGORISED_LABEL)
                    if row.stock_item_id is not None
                    else _UNCATEGORISED_LABEL
                )
                by_category[category] = by_category.get(category, 0.0) + unit_price * qty
            return by_category, sum(by_category.values())

        current_totals, current_total = _for_window(current_since, None)
        previous_totals, previous_total = _for_window(previous_since, previous_until)

        categories = set(current_totals) | set(previous_totals)
        rows: list[SpendYoYCategoryRow] = []
        for category in categories:
            current = current_totals.get(category, 0.0)
            previous = previous_totals.get(category, 0.0)
            delta = current - previous
            delta_pct: float | None
            if previous > 0:
                delta_pct = round((delta / previous) * 100, 1)
            else:
                # Undefined when the prior window had zero spend in this
                # category — a "new" category has no rate-of-change. P3
                # Honest: don't render "+∞%" or "+100%" for that case.
                delta_pct = None
            rows.append(SpendYoYCategoryRow(
                category=category,
                current=round(current, 2),
                previous=round(previous, 2),
                delta=round(delta, 2),
                delta_pct=delta_pct,
            ))
        # Rank by absolute delta magnitude so the biggest movers surface
        # first, positive OR negative — the user cares "what moved?".
        rows.sort(key=lambda r: (-abs(r.delta), r.category.lower()))

        overall_delta = current_total - previous_total
        overall_delta_pct: float | None
        if previous_total > 0:
            overall_delta_pct = round((overall_delta / previous_total) * 100, 1)
        else:
            overall_delta_pct = None

        return {
            "current_total": round(current_total, 2),
            "previous_total": round(previous_total, 2),
            "delta": round(overall_delta, 2),
            "delta_pct": overall_delta_pct,
            "rows": [asdict(r) for r in rows],
        }


@REPORTS_ROUTER.route("/spend-year-over-year", methods=["GET"])
def spend_year_over_year():
    raw = request.args.get("range", "1y")
    days = _range_days(raw)
    if days is None:
        return bad_request("range=all is not supported for spend-year-over-year — pick a bounded window.")
    now = datetime.now(timezone.utc)
    current_since = now - timedelta(days=days)
    previous_since = now - timedelta(days=days * 2)
    previous_until = current_since
    payload = SpendYoYHandler(SqlAlchemyRepository()).handle(
        current_since, previous_since, previous_until,
    )
    return ok({
        "range": raw,
        "window_days": days,
        **payload,
    })
