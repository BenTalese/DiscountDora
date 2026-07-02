"""P8-05 — "Should I buy this?" oracle.

    GET /api/stock-items/<id>/buy-verdict

Returns a per-item verdict {buy / wait / skip / unsure} plus confidence,
per-axis reasons, a one-tap action, and the data the composer reasoned
from. See `docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md` for the
full charter alignment + composition rules.

Design points that keep this honest:

* **Personal data only.** Price samples come from completed shopping-
  list lines via the existing `line_paid_unit_price` ladder (R-003
  chokepoint). Cadence is derived inline. Waste rate reads
  `StockItemWasteEvent`. No external calls, no crowd data.
* **Pure composer.** The axes are three pure functions
  (`_price_axis`, `_need_axis`, `_waste_axis`) that never touch a
  session; the endpoint fetches raw data once and passes it in. Tests
  drive the composer with fixture dataclasses — no DB, no HTTP.
* **Thin data collapses to `unsure`.** Charter P3 (Honest) + P12
  (No-invent) — the composer never fabricates a verdict from one
  sample.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DONE, ShoppingList, ShoppingListLine,
)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_waste_event import StockItemWasteEvent
from dora_api.domain.stock_status import (
    is_low_stock, is_out_of_stock,
)
from dora_api.features.app_settings.clock import household_today
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.features.shopping_lists._line_price import line_paid_unit_price
from dora_api.infrastructure.api_response import not_found, ok
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_LOGGER = logging.getLogger(__name__)


# ── Tunables (single source, easy to iterate) ─────────────────────────

# Thin-data thresholds — see the proposal §2.3.
_MIN_PRICE_SAMPLES = 3
_MIN_UNIQUE_PURCHASE_DATES = 2
_MIN_PURCHASES_FOR_WASTE_RATE = 3

# "Cheapest in 3 months" and "usual price" bands. Both expressed as
# multiples of the trimmed-mean price so a heavy tail doesn't skew the
# call ("cheapest in months" needs to be materially cheaper, not $0.02
# under mean).
_CHEAP_BAND_FRACTION = 0.92    # ≤ 92% of usual → "cheapest"
_ABOVE_BAND_FRACTION = 1.08    # ≥ 108% of usual → "above usual"

# Waste-rate bands (events ÷ purchases over last 12 months).
_WASTES_OFTEN_RATE = 0.40
_WASTES_SOMETIMES_RATE = 0.10

# 12-month window for both price + waste rate; the shopping app is
# personal and seasonal, and a year is the smallest window that catches
# household patterns like "we only buy soy sauce every 6 months".
_HISTORY_WINDOW_DAYS = 365
_PRICE_RECENT_WINDOW_DAYS = 90   # "cheapest in 3 months" window


# ── DTOs — one shape shared by the composer + the response ────────────


@dataclass(frozen=True, slots=True)
class VerdictReasonDto:
    axis: str      # "price" | "need" | "waste"
    signal: str    # see PROPOSAL §2.3
    label: str
    detail: Optional[str] = None


@dataclass(frozen=True, slots=True)
class OneTapActionDto:
    kind: str      # "add_to_list" | "skip" | "mark_stocked" |
                   # "remove_from_list" | "none"
    label: str


@dataclass(frozen=True, slots=True)
class VerdictDataUsedDto:
    price_samples: int
    price_average: Optional[float]
    price_last: Optional[float]
    price_last_at: Optional[str]           # ISO date; SPA-friendly
    days_since_last_purchase: Optional[int]
    average_days_between_purchase: Optional[float]
    waste_events_last_12mo: int
    purchases_last_12mo: int
    stock_level_band: str                   # "out" | "low" | "stocked" | "unknown"


@dataclass(frozen=True, slots=True)
class BuyVerdictDto:
    verdict: str                # "buy" | "wait" | "skip" | "unsure"
    confidence: str             # "high" | "medium" | "low"
    reasons: list[VerdictReasonDto]
    one_tap_action: OneTapActionDto
    data_used: VerdictDataUsedDto


# ── Raw inputs (fetched once by the endpoint, passed to composer) ─────


@dataclass(slots=True)
class _AxisInputs:
    # Prices are (unit_price, completed_at) tuples over the 12-month
    # window. Sorted newest-first.
    price_samples: list[tuple[float, datetime]] = field(default_factory=list)
    # Unique purchase dates over the window — used for cadence.
    unique_purchase_dates: list[date] = field(default_factory=list)
    waste_events_12mo: int = 0
    purchases_12mo: int = 0     # size of unique_purchase_dates
    stock_level_band: str = "unknown"        # "out" | "low" | "stocked" | "unknown"
    is_on_open_list: bool = False            # drives one_tap_action for "skip"
    today: date = field(default_factory=date.today)


# ── Per-axis composers — pure, testable ───────────────────────────────


def _trimmed_mean(values: list[float]) -> float:
    """Drop the single min + single max before averaging when we have
    ≥ 5 samples. Robust enough for household-scale shopping data
    without pulling in numpy."""
    if not values:
        return 0.0
    if len(values) >= 5:
        sorted_v = sorted(values)
        trimmed = sorted_v[1:-1]
        return sum(trimmed) / len(trimmed)
    return sum(values) / len(values)


def _price_axis(inputs: _AxisInputs) -> tuple[Optional[VerdictReasonDto], str]:
    """Return (reason, signal). `signal` is always set so the composer
    can key off it; `reason` is None when the axis contributes nothing
    (thin data)."""
    samples = inputs.price_samples
    if len(samples) < _MIN_PRICE_SAMPLES:
        return None, "thin_data"

    prices = [p for p, _ in samples]
    usual = _trimmed_mean(prices)
    last_price, last_at = samples[0]
    horizon = (
        datetime.combine(inputs.today, datetime.min.time(), tzinfo=timezone.utc)
        - timedelta(days=_PRICE_RECENT_WINDOW_DAYS)
    )
    recent = [p for p, ts in samples if ts >= horizon]
    recent_min = min(recent) if recent else last_price

    if last_price <= _CHEAP_BAND_FRACTION * usual and last_price <= recent_min:
        return VerdictReasonDto(
            axis="price",
            signal="cheapest_3mo",
            label="Cheapest you've paid in 3 months",
            detail=f"${last_price:.2f} last shop · usually ${usual:.2f}",
        ), "cheapest_3mo"
    if last_price >= _ABOVE_BAND_FRACTION * usual:
        return VerdictReasonDto(
            axis="price",
            signal="above_usual",
            label="Above your usual price",
            detail=f"${last_price:.2f} last shop · usually ${usual:.2f}",
        ), "above_usual"
    return VerdictReasonDto(
        axis="price",
        signal="usual_price",
        label="Usual price",
        detail=f"${last_price:.2f} last shop · usually ${usual:.2f}",
    ), "usual_price"


def _need_axis(inputs: _AxisInputs) -> tuple[Optional[VerdictReasonDto], str]:
    band = inputs.stock_level_band
    if band == "out":
        return VerdictReasonDto(
            axis="need",
            signal="out_of_stock",
            label="You're out of stock",
        ), "out_of_stock"
    if band == "low":
        detail = _cadence_detail(inputs)
        return VerdictReasonDto(
            axis="need",
            signal="low_stock",
            label="Running low",
            detail=detail,
        ), "low_stock"
    if band == "stocked":
        detail = _cadence_detail(inputs)
        return VerdictReasonDto(
            axis="need",
            signal="well_stocked",
            label="Well stocked",
            detail=detail,
        ), "well_stocked"
    # Unknown stock band means we don't have a status at all — treat as
    # thin-data on this axis; the composer will absorb the drop in
    # confidence.
    return None, "thin_data"


def _cadence_detail(inputs: _AxisInputs) -> Optional[str]:
    dates = inputs.unique_purchase_dates
    if len(dates) < _MIN_UNIQUE_PURCHASE_DATES:
        return None
    gaps = [
        (dates[i] - dates[i - 1]).days
        for i in range(1, len(dates))
        if (dates[i] - dates[i - 1]).days > 0
    ]
    if not gaps:
        return None
    avg_days = sum(gaps) / len(gaps)
    days_since = (inputs.today - dates[-1]).days
    if days_since >= avg_days:
        return f"Bought every ~{avg_days:.0f} days · last shop {days_since} days ago"
    remaining = max(0, int(round(avg_days - days_since)))
    return f"Bought every ~{avg_days:.0f} days · ~{remaining} days to run-out"


def _waste_axis(inputs: _AxisInputs) -> tuple[Optional[VerdictReasonDto], str]:
    if inputs.purchases_12mo < _MIN_PURCHASES_FOR_WASTE_RATE:
        # Not enough purchase history to compute a rate. Distinguish
        # "we've never seen you waste this" from "we don't know" via
        # the events count.
        if inputs.waste_events_12mo == 0:
            return None, "no_waste_history"
        return None, "thin_data"

    rate = inputs.waste_events_12mo / inputs.purchases_12mo
    if rate >= _WASTES_OFTEN_RATE:
        return VerdictReasonDto(
            axis="waste",
            signal="wastes_often",
            label=f"You've wasted this {int(round(rate * 100))}% of the time",
            detail=(
                f"{inputs.waste_events_12mo} thrown away vs "
                f"{inputs.purchases_12mo} purchased (last 12 months)"
            ),
        ), "wastes_often"
    if rate >= _WASTES_SOMETIMES_RATE:
        return VerdictReasonDto(
            axis="waste",
            signal="wastes_sometimes",
            label="Occasionally goes to waste",
            detail=(
                f"{inputs.waste_events_12mo} thrown away vs "
                f"{inputs.purchases_12mo} purchased (last 12 months)"
            ),
        ), "wastes_sometimes"
    return None, "no_waste_history"


# ── The composer itself ────────────────────────────────────────────────


def compose_verdict(inputs: _AxisInputs) -> BuyVerdictDto:
    price_reason, price_signal = _price_axis(inputs)
    need_reason,  need_signal  = _need_axis(inputs)
    waste_reason, waste_signal = _waste_axis(inputs)

    reasons: list[VerdictReasonDto] = []
    for r in (need_reason, price_reason, waste_reason):
        if r is not None:
            reasons.append(r)

    thin = [s for s in (price_signal, need_signal, waste_signal) if s == "thin_data"]

    # Charter §2.3 rule set.
    verdict = "unsure"
    confidence = "medium"

    if need_signal == "out_of_stock":
        verdict, confidence = "buy", "high"
    elif need_signal == "low_stock":
        if price_signal == "cheapest_3mo":
            verdict, confidence = "buy", "high"
        elif price_signal == "above_usual":
            verdict, confidence = "wait", "medium"
        else:
            verdict, confidence = "buy", "medium"
    elif need_signal == "well_stocked":
        if waste_signal == "wastes_often":
            verdict, confidence = "skip", "high"
        elif price_signal == "cheapest_3mo":
            verdict, confidence = "buy", "medium"
        elif price_signal == "above_usual":
            verdict, confidence = "wait", "medium"
        else:
            verdict, confidence = "unsure", "low"
    else:
        # need is thin_data → everything hinges on price alone, which is
        # not enough for a strong call.
        verdict, confidence = "unsure", "low"

    # Any thin axis drops confidence one step. Three thin axes are
    # collapsed to a single explicit "not enough history" reason so the
    # user sees one honest message rather than a wall of blanks.
    if len(thin) == 3:
        return BuyVerdictDto(
            verdict="unsure",
            confidence="low",
            reasons=[VerdictReasonDto(
                axis="need",
                signal="thin_data",
                label="Not enough history yet",
                detail="Log a few shops or waste events and Dora will start weighing in.",
            )],
            one_tap_action=OneTapActionDto(kind="none", label=""),
            data_used=_data_used_dto(inputs),
        )
    if thin:
        confidence = _step_down(confidence)

    one_tap = _pick_action(verdict, inputs)
    return BuyVerdictDto(
        verdict=verdict,
        confidence=confidence,
        reasons=reasons,
        one_tap_action=one_tap,
        data_used=_data_used_dto(inputs),
    )


def _step_down(confidence: str) -> str:
    return {"high": "medium", "medium": "low", "low": "low"}[confidence]


def _pick_action(verdict: str, inputs: _AxisInputs) -> OneTapActionDto:
    if verdict == "buy":
        return OneTapActionDto(kind="add_to_list", label="Add to primary list")
    if verdict == "skip":
        if inputs.is_on_open_list:
            return OneTapActionDto(kind="remove_from_list", label="Remove from list")
        # Well-stocked + wasteful ⇒ nudge to close the loop on inventory.
        return OneTapActionDto(kind="mark_stocked", label="Already stocked")
    if verdict == "wait":
        return OneTapActionDto(kind="skip", label="Skip for now")
    # `unsure` — no action; the user makes the call.
    return OneTapActionDto(kind="none", label="")


def _data_used_dto(inputs: _AxisInputs) -> VerdictDataUsedDto:
    price_average: Optional[float] = None
    price_last: Optional[float] = None
    price_last_at: Optional[str] = None
    if inputs.price_samples:
        prices = [p for p, _ in inputs.price_samples]
        price_average = round(_trimmed_mean(prices), 2)
        price_last = round(inputs.price_samples[0][0], 2)
        price_last_at = inputs.price_samples[0][1].date().isoformat()

    days_since: Optional[int] = None
    avg_days: Optional[float] = None
    dates = inputs.unique_purchase_dates
    if dates:
        days_since = max(0, (inputs.today - dates[-1]).days)
    if len(dates) >= _MIN_UNIQUE_PURCHASE_DATES:
        gaps = [
            (dates[i] - dates[i - 1]).days
            for i in range(1, len(dates))
            if (dates[i] - dates[i - 1]).days > 0
        ]
        if gaps:
            avg_days = round(sum(gaps) / len(gaps), 1)

    return VerdictDataUsedDto(
        price_samples=len(inputs.price_samples),
        price_average=price_average,
        price_last=price_last,
        price_last_at=price_last_at,
        days_since_last_purchase=days_since,
        average_days_between_purchase=avg_days,
        waste_events_last_12mo=inputs.waste_events_12mo,
        purchases_last_12mo=inputs.purchases_12mo,
        stock_level_band=inputs.stock_level_band,
    )


# ── Data gathering (the only part that touches the repo) ──────────────


def _stock_level_band(item: StockItem) -> str:
    level = item.stock_level
    if level is None:
        return "unknown"
    if is_out_of_stock(level):
        return "out"
    if is_low_stock(level):
        return "low"
    return "stocked"


def _gather_inputs(
    repository: SqlAlchemyRepository, item: StockItem,
) -> _AxisInputs:
    today = household_today(repository)
    horizon_start = datetime.combine(
        today - timedelta(days=_HISTORY_WINDOW_DAYS),
        datetime.min.time(), tzinfo=timezone.utc,
    )

    # Completed-list lines for this item.
    lines: list[ShoppingListLine] = repository.get(ShoppingListLine).all(
        EntityField(ShoppingListLine, ShoppingListLine.Fields.STOCK_ITEM_ID).eq(item.id)
    )
    list_ids = list({l.shopping_list_id for l in lines})
    completed_lookup: dict[UUID, datetime | None] = {}
    open_list_ids: set[UUID] = set()
    if list_ids:
        lists = repository.get(ShoppingList).all(
            EntityField(ShoppingList, "id").in_(list_ids)
        )
        for l in lists:
            if l.status == SHOPPING_LIST_STATUS_DONE:
                completed_lookup[l.id] = l.completed_at
            else:
                open_list_ids.add(l.id)

    samples: list[tuple[float, datetime]] = []
    for line in lines:
        completed_at = completed_lookup.get(line.shopping_list_id)
        if completed_at is None:
            continue
        if completed_at < horizon_start:
            continue
        price = line_paid_unit_price(line)
        if price is None:
            continue
        samples.append((price, completed_at))
    samples.sort(key=lambda s: s[1], reverse=True)

    unique_dates = sorted({s[1].date() for s in samples})

    # Waste events over the same window.
    waste_events: list[StockItemWasteEvent] = repository.get(StockItemWasteEvent).all(
        EntityField(StockItemWasteEvent, StockItemWasteEvent.Fields.STOCK_ITEM_ID).eq(item.id)
    )
    waste_in_window = sum(
        1 for e in waste_events
        if e.occurred_at and e.occurred_at >= horizon_start
    )

    is_on_open_list = any(
        line.shopping_list_id in open_list_ids for line in lines
    )

    return _AxisInputs(
        price_samples=samples,
        unique_purchase_dates=unique_dates,
        waste_events_12mo=waste_in_window,
        purchases_12mo=len(unique_dates),
        stock_level_band=_stock_level_band(item),
        is_on_open_list=is_on_open_list,
        today=today,
    )


# ── Endpoint ───────────────────────────────────────────────────────────


@STOCK_ITEM_ROUTER.route("/<stock_item_id>/buy-verdict", methods=["GET"])
def get_buy_verdict(stock_item_id: UUID):
    repo = SqlAlchemyRepository()
    item: StockItem | None = (
        repo.get(StockItem).include(StockItem.Fields.STOCK_LEVEL).by_id(stock_item_id)
    )
    if item is None:
        return not_found("StockItem", stock_item_id)
    inputs = _gather_inputs(repo, item)
    verdict = compose_verdict(inputs)
    _LOGGER.debug(
        "buy-verdict %s → %s/%s (%d reasons, %d price samples, %d waste events)",
        stock_item_id, verdict.verdict, verdict.confidence,
        len(verdict.reasons), inputs.purchases_12mo, inputs.waste_events_12mo,
    )
    return ok(verdict)
