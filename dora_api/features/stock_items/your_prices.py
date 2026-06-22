"""Server-derived "Your prices" baseline + signal (FU-227 chunk 4).

Owns the median / "above usual" math (C1/C2 — locked at median, 1.15×, min 3
samples, trailing 12 months). Per-dimension grouping (B4) — observations
logged in volume vs mass vs count get separate baselines and the most-recent
dimension wins for the headline. **LC-2 source-blind:** ``sample_count``
counts observations only — offers never contribute to the baseline median
even when products are on. They show up in the offers sidecar instead (a
separate UI region in the widget; "Current shelf prices: …"), so a flash
sale doesn't poison the user's baseline.

R-003: this module is the single place baseline math lives. The client never
re-derives — it renders ``baseline`` / ``current`` / ``above_baseline`` from
the DTO straight to the screen.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID


def _as_naive_utc(dt: datetime) -> datetime:
    """SQLite strips tzinfo on read, so observation `observed_at` comes back
    naive even though the writer stores UTC. The cutoff is built with
    `datetime.now(timezone.utc)` so it's aware. Make both naive (UTC-rooted)
    before comparing — otherwise `<` raises TypeError. R-005 carve-out: the
    Postgres-portable fix would be a tz-aware column read, but until the
    Postgres migration (FU-045) we live with this and centralise the
    coercion here."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

from dora_api.domain import units
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.domain.entities.stock_item_price_observation import \
    StockItemPriceObservation
from dora_api.domain.entities.store import Store
from dora_api.persistence.field import EntityField


# Tunable constants — module-level so they're discoverable for review.
MIN_SAMPLES: int = 3
ABOVE_THRESHOLD: float = 1.15
BASELINE_WINDOW: timedelta = timedelta(days=365)


@dataclass(frozen=True, slots=True)
class OfferSidecarEntry:
    """A single "what stores are listing right now" entry. Lives next to
    the baseline widget but is **never** folded into the median (LC-2)."""
    store_name: str
    price_per_unit: float       # normalised to the active dimension's canonical unit
    unit: str                   # the canonical unit string ("L", "kg", "ea")


@dataclass(frozen=True, slots=True)
class YourPrices:
    """Server-derived signal for a single stock item.

    Empty state (no observations): every numeric field is ``None`` /
    ``False`` / ``0``; the widget renders the empty-state copy.
    Below MIN_SAMPLES: ``baseline`` / ``above_baseline`` stay null/false,
    but ``current`` may be set so the widget shows a "Last seen $X" line.
    Above MIN_SAMPLES: full output; ``above_baseline`` is **strictly**
    greater than ``baseline * ABOVE_THRESHOLD`` (edge case is NOT above).
    """
    baseline: float | None
    baseline_unit: str | None       # "L" / "kg" / "ea" — never the raw alias
    current: float | None
    above_baseline: bool
    sample_count: int               # observations only (LC-2)
    last_observed_at: datetime | None
    last_seen_store_name: str | None
    offers_sidecar: list[OfferSidecarEntry]


def _per_unit_in_canonical(
    *, total_price: float, total_measure: float, unit: str,
) -> tuple[float, str] | None:
    """Convert one observation to (per-unit-price, canonical-unit).

    Returns None when the unit is unknown or the measure is zero. The
    canonical unit is the dimension's display denominator
    (``L`` / ``kg`` / ``ea``) — every observation in the same dimension
    lands on the same denominator so the median is comparable.
    """
    if total_measure <= 0:
        return None
    udef = units.find_unit(unit)
    if udef is None or udef.dimension not in units.PRICE_DIMENSIONS:
        return None
    canonical = units.CANONICAL_PRICE_UNIT[udef.dimension]
    measure_in_canonical = units.convert(total_measure, unit, canonical)
    if measure_in_canonical is None or measure_in_canonical <= 0:
        return None
    return total_price / measure_in_canonical, canonical


def build_your_prices_for_item(
    repo, stock_item_id: UUID, *, now: datetime | None = None,
) -> YourPrices:
    """Build the YourPrices signal for one stock item.

    Algorithm (B4 / C1-C5 / LC-2):
      1. Load all observations for the item; if empty → empty state.
      2. Active dimension = dimension of most-recent observation.
      3. Filter to obs in that dimension within ``BASELINE_WINDOW`` ago.
      4. Normalise each to per-canonical-unit price.
      5. ``current`` = most-recent obs's per-unit price (always set if
         there's any obs at all — even if too few for a baseline).
      6. ``sample_count`` < MIN_SAMPLES → baseline None, above_baseline
         False. Else median + strict-greater threshold compare.
      7. ``offers_sidecar`` (LC-2) — populated from linked products'
         current offers (when present), normalised to the same canonical
         unit. Never contributes to the median.
    """
    _now = now or datetime.now(timezone.utc)

    observations: list[StockItemPriceObservation] = repo.get(StockItemPriceObservation).all(
        EntityField(
            StockItemPriceObservation,
            StockItemPriceObservation.Fields.STOCK_ITEM_ID,
        ).eq(stock_item_id)
    )
    if not observations:
        return YourPrices(
            baseline=None, baseline_unit=None, current=None,
            above_baseline=False, sample_count=0,
            last_observed_at=None, last_seen_store_name=None,
            offers_sidecar=[],
        )

    observations.sort(key=lambda o: o.observed_at, reverse=True)
    latest = observations[0]
    latest_def = units.find_unit(latest.unit)
    if latest_def is None or latest_def.dimension not in units.PRICE_DIMENSIONS:
        # Defensive — the write path validates this so it's a "should never"
        # case; degrade to empty state rather than 500.
        return YourPrices(
            baseline=None, baseline_unit=None, current=None,
            above_baseline=False, sample_count=0,
            last_observed_at=latest.observed_at,
            last_seen_store_name=None,
            offers_sidecar=[],
        )
    active_dim = latest_def.dimension
    canonical_unit = units.CANONICAL_PRICE_UNIT[active_dim]

    latest_per_unit = _per_unit_in_canonical(
        total_price=latest.total_price,
        total_measure=latest.total_measure,
        unit=latest.unit,
    )
    current_value = latest_per_unit[0] if latest_per_unit else None

    # Resolve the most-recent observation's store name (A2 — surfaced in the
    # widget's "Last seen $X at Coles" line).
    last_seen_store_name: str | None = None
    if latest.store_id is not None:
        store = repo.get(Store).by_id(latest.store_id)
        if store is not None:
            last_seen_store_name = store.name

    # Build the dimension-filtered, window-filtered, normalised series for
    # the median.
    cutoff = _as_naive_utc(_now - BASELINE_WINDOW)
    in_dim_window: list[float] = []
    for obs in observations:
        obs_def = units.find_unit(obs.unit)
        if obs_def is None or obs_def.dimension != active_dim:
            continue
        if _as_naive_utc(obs.observed_at) < cutoff:
            continue
        pu = _per_unit_in_canonical(
            total_price=obs.total_price,
            total_measure=obs.total_measure,
            unit=obs.unit,
        )
        if pu is not None:
            in_dim_window.append(pu[0])

    sample_count = len(in_dim_window)

    baseline: float | None = None
    above: bool = False
    if sample_count >= MIN_SAMPLES:
        baseline = statistics.median(in_dim_window)
        # "Strictly greater" per the C2 edge-case test (current == baseline*1.15
        # is NOT above) — keeps the warning chip from flashing on round-number
        # ties.
        if current_value is not None:
            above = current_value > baseline * ABOVE_THRESHOLD

    # LC-2 offers sidecar — never folded into the median above. Populated
    # only when there are linked products with a current offer.
    offers = _build_offers_sidecar(repo, stock_item_id, canonical_unit=canonical_unit)

    return YourPrices(
        baseline=baseline,
        baseline_unit=canonical_unit if baseline is not None else None,
        current=current_value,
        above_baseline=above,
        sample_count=sample_count,
        last_observed_at=latest.observed_at,
        last_seen_store_name=last_seen_store_name,
        offers_sidecar=offers,
    )


def build_your_prices_for_product(
    repo, product_id: UUID, *, now: datetime | None = None,
) -> YourPrices:
    """Per-product variant used by the Price-History page (chunk 6).

    Same baseline math, but the "observations" pool is gathered transitively
    — every stock-item linked to this product contributes its observations.
    Used by Price-History chart to render a baseline reference line per
    product series (F-3) and the above-usual annotation in the header.
    """
    # FU-227 chunk 6 will wire this end-to-end. The chunk-4 implementation
    # is intentionally minimal: aggregate observations across linked stock
    # items and reuse the per-item algorithm. No offers sidecar here — the
    # per-product Price-History page already shows offers as the primary
    # series, sidecar would be redundant.
    from dora_api.domain.entities.stock_item import StockItem
    from sqlalchemy import select
    from dora_api.app import db

    # Fetch linked stock-item ids via the StockItemProduct join table.
    # Pure SQL via the metadata table rather than an entity since the join
    # table isn't mapped to a domain entity.
    join_table = db.metadata.tables["StockItemProduct"]
    stock_item_ids: list[UUID] = [
        row[0]
        for row in db.session.execute(
            select(join_table.c.stock_item_id).where(
                join_table.c.product_id == product_id
            )
        ).all()
    ]
    if not stock_item_ids:
        return YourPrices(
            baseline=None, baseline_unit=None, current=None,
            above_baseline=False, sample_count=0,
            last_observed_at=None, last_seen_store_name=None,
            offers_sidecar=[],
        )

    _now = now or datetime.now(timezone.utc)
    observations: list[StockItemPriceObservation] = repo.get(StockItemPriceObservation).all(
        EntityField(
            StockItemPriceObservation,
            StockItemPriceObservation.Fields.STOCK_ITEM_ID,
        ).in_(stock_item_ids)
    )
    if not observations:
        return YourPrices(
            baseline=None, baseline_unit=None, current=None,
            above_baseline=False, sample_count=0,
            last_observed_at=None, last_seen_store_name=None,
            offers_sidecar=[],
        )

    observations.sort(key=lambda o: o.observed_at, reverse=True)
    latest = observations[0]
    latest_def = units.find_unit(latest.unit)
    if latest_def is None or latest_def.dimension not in units.PRICE_DIMENSIONS:
        return YourPrices(
            baseline=None, baseline_unit=None, current=None,
            above_baseline=False, sample_count=0,
            last_observed_at=latest.observed_at,
            last_seen_store_name=None,
            offers_sidecar=[],
        )
    active_dim = latest_def.dimension
    canonical_unit = units.CANONICAL_PRICE_UNIT[active_dim]

    cutoff = _as_naive_utc(_now - BASELINE_WINDOW)
    in_dim_window: list[float] = []
    for obs in observations:
        obs_def = units.find_unit(obs.unit)
        if obs_def is None or obs_def.dimension != active_dim:
            continue
        if _as_naive_utc(obs.observed_at) < cutoff:
            continue
        pu = _per_unit_in_canonical(
            total_price=obs.total_price,
            total_measure=obs.total_measure,
            unit=obs.unit,
        )
        if pu is not None:
            in_dim_window.append(pu[0])

    latest_pu = _per_unit_in_canonical(
        total_price=latest.total_price,
        total_measure=latest.total_measure,
        unit=latest.unit,
    )
    current_value = latest_pu[0] if latest_pu else None

    last_seen_store_name: str | None = None
    if latest.store_id is not None:
        store = repo.get(Store).by_id(latest.store_id)
        if store is not None:
            last_seen_store_name = store.name

    sample_count = len(in_dim_window)
    baseline: float | None = None
    above: bool = False
    if sample_count >= MIN_SAMPLES:
        baseline = statistics.median(in_dim_window)
        if current_value is not None:
            above = current_value > baseline * ABOVE_THRESHOLD

    return YourPrices(
        baseline=baseline,
        baseline_unit=canonical_unit if baseline is not None else None,
        current=current_value,
        above_baseline=above,
        sample_count=sample_count,
        last_observed_at=latest.observed_at,
        last_seen_store_name=last_seen_store_name,
        offers_sidecar=[],
    )


def _build_offers_sidecar(
    repo, stock_item_id: UUID, *, canonical_unit: str,
) -> list[OfferSidecarEntry]:
    """LC-2 — "Current shelf prices: $X at Y · $Z at W" for products users.

    Reads the current offers of every linked product, normalised to the
    same canonical unit as the baseline so they're directly comparable
    visually. Never returns offers in a different dimension than the
    baseline (a sized product in ml can't sit next to a count baseline).
    """
    from sqlalchemy import select
    from dora_api.app import db

    join_table = db.metadata.tables["StockItemProduct"]
    product_ids: list[UUID] = [
        row[0]
        for row in db.session.execute(
            select(join_table.c.product_id).where(
                join_table.c.stock_item_id == stock_item_id
            )
        ).all()
    ]
    if not product_ids:
        return []

    products: Iterable[Product] = repo.get(Product).all(
        EntityField(Product, "id").in_(product_ids)
    )

    target_dim_unit = units.find_unit(canonical_unit)
    target_dim = target_dim_unit.dimension if target_dim_unit else None

    out: list[OfferSidecarEntry] = []
    for prod in products:
        if not prod.is_active or not prod.is_available:
            continue
        offer: ProductOffer | None = prod.current_offer
        if offer is None or offer.price_now is None or offer.price_now <= 0:
            continue
        if not prod.size_unit or not prod.size_value or prod.size_value <= 0:
            continue
        # Skip offers in a different dimension to the baseline (e.g. a
        # "12 ea" pack offer when the baseline is per-L) — they'd just
        # confuse the sidebar.
        offer_unit = units.find_unit(prod.size_unit)
        if offer_unit is None or offer_unit.dimension != target_dim:
            continue
        size_in_canonical = units.convert(prod.size_value, prod.size_unit, canonical_unit)
        if size_in_canonical is None or size_in_canonical <= 0:
            continue
        per_unit = float(offer.price_now) / size_in_canonical
        store_name = prod.store.name if prod.store else "Unknown store"
        out.append(OfferSidecarEntry(
            store_name=store_name,
            price_per_unit=per_unit,
            unit=canonical_unit,
        ))
    # Cheapest first — what users care about most is the deal.
    out.sort(key=lambda e: e.price_per_unit)
    return out
