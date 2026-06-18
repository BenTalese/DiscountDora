"""N8 — Price History Explorer backend.

  GET    /api/price-history?product_ids=<csv>&range=30d|90d|1y|all
  POST   /api/price-history/alerts          — body {product_id, threshold_unit_price}
  GET    /api/price-history/alerts          — list current user's alerts
  DELETE /api/price-history/alerts/<id>     — remove

Price points are pulled from `ProductHistoricOffer` (the append-only
log fed by `POST /api/ingest`). The current point comes from the live
`ProductOffer` row. All-time low is computed across the historic rows.

Alerts are per-user; the trigger-side logic (firing a notification on
the next push that beats the threshold) is owned by whatever ingestion
producer the install runs — this round just creates / lists / removes
the subscription rows.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from flask import request, session
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select

from dora_api.app import db
from dora_api.domain.entities.price_alert import PriceAlert
from dora_api.features.routers import PRICE_HISTORY_ROUTER
from dora_api.infrastructure.api_response import (bad_request, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_RANGE_DAYS = {"30d": 30, "90d": 90, "1y": 365}


def _range_cutoff(value: str | None) -> datetime | None:
    """`None` = "all" (no cutoff). Otherwise returns the earliest
    timestamp we'll include points from."""
    if not value or value == "all":
        return None
    days = _RANGE_DAYS.get(value)
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


def _parse_product_ids(raw: str | None) -> list[UUID]:
    if not raw:
        return []
    out: list[UUID] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.append(UUID(token))
        except (ValueError, TypeError):
            continue
    return out


def _current_user_id() -> UUID | None:
    raw = session.get("user_id")
    if not raw:
        return None
    try:
        return UUID(raw)
    except (ValueError, TypeError):
        return None


# ── GET /api/price-history ────────────────────────────────────────────

@PRICE_HISTORY_ROUTER.route("", methods=["GET"])
def get_price_history():
    _Logger = logging.getLogger(__name__)
    ids = _parse_product_ids(request.args.get("product_ids"))
    if not ids:
        return bad_request("Provide one or more product_ids (comma-separated UUIDs).")
    if len(ids) > 5:
        return bad_request("At most 5 products at a time.")

    cutoff = _range_cutoff(request.args.get("range"))

    product_table = db.metadata.tables["Product"]
    merchant_table = db.metadata.tables["Merchant"]
    offer_table = db.metadata.tables["ProductOffer"]
    historic_table = db.metadata.tables["ProductHistoricOffer"]

    products = db.session.execute(
        select(
            product_table.c.id, product_table.c.name,
            product_table.c.size_value, product_table.c.size_unit,
            merchant_table.c.name.label("merchant_name"),
        ).select_from(
            product_table.join(merchant_table, product_table.c.merchant_id == merchant_table.c.id)
        ).where(product_table.c.id.in_(ids))
    ).mappings().all()
    products_by_id = {row["id"]: dict(row) for row in products}

    # Historic points per product.
    where_clauses = [historic_table.c.product_id.in_(ids)]
    if cutoff is not None:
        where_clauses.append(historic_table.c.offered_on >= cutoff)
    historic_rows = db.session.execute(
        select(historic_table).where(and_(*where_clauses)).order_by(
            historic_table.c.product_id, historic_table.c.offered_on,
        )
    ).mappings().all()

    # Live offers (current).
    current_rows = db.session.execute(
        select(offer_table).where(offer_table.c.product_id.in_(ids))
    ).mappings().all()
    current_by_product = {row["product_id"]: dict(row) for row in current_rows}

    # All-time-low needs the full history regardless of range.
    atl_where = [historic_table.c.product_id.in_(ids)]
    all_history = db.session.execute(
        select(historic_table).where(and_(*atl_where))
    ).mappings().all()
    atl_by_product: dict[Any, dict[str, Any]] = {}
    for row in all_history:
        pid = row["product_id"]
        price = row["price_now"]
        if price is None:
            continue
        prev = atl_by_product.get(pid)
        if prev is None or price < prev["unit_price"]:
            atl_by_product[pid] = {
                "unit_price": float(price),
                "date": (row["offered_on"].isoformat() if row["offered_on"] else None),
            }

    series: list[dict[str, Any]] = []
    points_by_product: dict[Any, list[dict[str, Any]]] = {pid: [] for pid in ids}
    for row in historic_rows:
        pid = row["product_id"]
        if pid not in points_by_product:
            continue
        points_by_product[pid].append({
            "date": row["offered_on"].isoformat() if row["offered_on"] else None,
            "unit_price": float(row["price_now"]) if row["price_now"] is not None else None,
            "list_price": float(row["price_was"]) if row["price_was"] is not None else None,
            "on_deal": (
                row["price_now"] is not None
                and row["price_was"] is not None
                and row["price_now"] < row["price_was"]
            ),
        })

    for pid in ids:
        product = products_by_id.get(pid)
        if product is None:
            # The caller asked for a product that doesn't exist —
            # surface a placeholder so the SPA can render "no data".
            series.append({
                "product_id": str(pid), "name": "(unknown)", "merchant": "",
                "points": [], "current": None, "all_time_low": None,
            })
            continue
        current = current_by_product.get(pid)
        deal_pct = None
        if current and current.get("price_now") and current.get("price_was"):
            try:
                pct = (1.0 - (current["price_now"] / current["price_was"])) * 100.0
                deal_pct = max(0, int(round(pct)))
            except (TypeError, ZeroDivisionError):
                deal_pct = None
        series.append({
            "product_id": str(pid),
            "name": product["name"],
            "merchant": product["merchant_name"] or "",
            "points": points_by_product.get(pid, []),
            "current": (
                {
                    "unit_price": float(current["price_now"]) if current and current.get("price_now") is not None else None,
                    "list_price": float(current["price_was"]) if current and current.get("price_was") is not None else None,
                    "deal_pct": deal_pct,
                }
                if current else None
            ),
            "all_time_low": atl_by_product.get(pid),
        })

    _Logger.debug(
        "price_history requested ids=%s range=%s", ids, request.args.get("range"),
    )
    return ok({"series": series})


# ── Alerts ────────────────────────────────────────────────────────────

class CreatePriceAlertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: UUID
    threshold_unit_price: float = Field(gt=0)


@PRICE_HISTORY_ROUTER.route("/alerts", methods=["POST"])
@has_request_body(CreatePriceAlertRequest)
def create_price_alert():
    user_id = _current_user_id()
    if user_id is None:
        return bad_request("Not signed in.")
    body: CreatePriceAlertRequest = get_request_body()

    repo = SqlAlchemyRepository()
    product_table = db.metadata.tables["Product"]
    if db.session.execute(
        select(product_table.c.id).where(product_table.c.id == body.product_id)
    ).first() is None:
        return not_found("Product", body.product_id)

    row = PriceAlert(
        user_id=user_id,
        product_id=body.product_id,
        threshold_unit_price=float(body.threshold_unit_price),
        created_at=datetime.now(timezone.utc),
    )
    repo.add(row)
    repo.save_changes()
    return ok({
        "price_alert_id": str(row.id),
        "product_id": str(body.product_id),
        "threshold_unit_price": float(body.threshold_unit_price),
        "created_at": row.created_at.isoformat(),
    })


@PRICE_HISTORY_ROUTER.route("/alerts", methods=["GET"])
def list_price_alerts():
    user_id = _current_user_id()
    if user_id is None:
        return bad_request("Not signed in.")
    alert_table = db.metadata.tables["PriceAlert"]
    product_table = db.metadata.tables["Product"]
    merchant_table = db.metadata.tables["Merchant"]
    rows = db.session.execute(
        select(
            alert_table.c.id, alert_table.c.product_id,
            alert_table.c.threshold_unit_price, alert_table.c.created_at,
            alert_table.c.last_fired_at,
            product_table.c.name.label("product_name"),
            merchant_table.c.name.label("merchant_name"),
        )
        .select_from(
            alert_table.join(product_table, alert_table.c.product_id == product_table.c.id)
            .join(merchant_table, product_table.c.merchant_id == merchant_table.c.id)
        )
        .where(alert_table.c.user_id == user_id)
        .order_by(alert_table.c.created_at.desc())
    ).mappings().all()
    return ok({
        "items": [
            {
                "price_alert_id": str(r["id"]),
                "product_id": str(r["product_id"]),
                "product_name": r["product_name"],
                "merchant_name": r["merchant_name"],
                "threshold_unit_price": float(r["threshold_unit_price"]),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "last_fired_at": r["last_fired_at"].isoformat() if r["last_fired_at"] else None,
            }
            for r in rows
        ],
    })


@PRICE_HISTORY_ROUTER.route("/alerts/<alert_id>", methods=["DELETE"])
def delete_price_alert(alert_id: str):
    user_id = _current_user_id()
    if user_id is None:
        return bad_request("Not signed in.")
    try:
        parsed = UUID(alert_id)
    except (ValueError, TypeError):
        return bad_request("alert_id must be a UUID.")
    alert_table = db.metadata.tables["PriceAlert"]
    # Scope by user so one account can't delete another's alerts.
    result = db.session.execute(
        alert_table.delete().where(
            alert_table.c.id == parsed,
            alert_table.c.user_id == user_id,
        )
    )
    db.session.commit()
    if (result.rowcount or 0) == 0:
        return not_found("PriceAlert", parsed)
    return no_content()
