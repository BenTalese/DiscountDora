"""Barcode + QR endpoints.

  GET    /api/stock-items/<id>/qr                — PNG of the item's dora:// QR
  GET    /api/stock-items/qr/sheet               — HTML print-sheet of many QRs
  GET    /api/data/barcodes/lookup?value=...     — disambiguate a scanned value
  POST   /api/data/barcodes                      — register a real barcode (FU-056)
  DELETE /api/data/barcodes/<id>                 — remove a registration

QR generation uses `qrcode[pil]` (pure Python + Pillow). The sheet
endpoint is HTML so the user can print or Save-as-PDF — consistent
with the no-server-PDF call we made in N4.

Model note (FU-056 hybrid): a real-world EAN can attach to a *Product* (1:1,
the catalogue case) AND/OR a *StockItem* (m:n, the lightweight-install +
direct-registration case). Both linkages coexist when present. Lookup
precedence prefers the most specific signal — direct stock-item linkage
wins over a Product traversal. Scanning is a navigation aid only; it never
does live deal lookup.
"""
import base64
import io
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlparse
from uuid import UUID

import qrcode
from flask import Response, render_template_string, request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.exc import IntegrityError

from dora_api.app import db
from dora_api.domain.entities.barcode import Barcode
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.data.export_shared import PRINT_CSS, PRINT_TOOLBAR
from dora_api.features.routers import (
    DATA_ROUTER, STOCK_ITEM_ROUTER,
)
from dora_api.infrastructure.api_response import (
    bad_request, no_content, not_found, ok,
    unprocessable_entity, ProblemDetails,
)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Sheet layouts. New layouts plug in here without touching the route.
@dataclass(frozen=True)
class SheetLayout:
    key: str
    label: str
    columns: int
    rows: int
    page_size: str           # CSS @page size string
    cell_width_mm: float
    cell_height_mm: float
    label_padding_mm: float


SHEET_LAYOUTS: dict[str, SheetLayout] = {
    "avery-5160": SheetLayout(
        key="avery-5160", label="Avery 5160 (US Letter, 3 × 10)",
        columns=3, rows=10, page_size="letter",
        cell_width_mm=66.7, cell_height_mm=25.4, label_padding_mm=2.5,
    ),
    "a4-21up": SheetLayout(
        key="a4-21up", label="A4 21-up (3 × 7)",
        columns=3, rows=7, page_size="A4",
        cell_width_mm=63.5, cell_height_mm=38.1, label_padding_mm=2.5,
    ),
}
DEFAULT_LAYOUT_KEY = "a4-21up"


DORA_SCHEME_PREFIX = "dora://stock-item/"
QR_DEFAULT_SIZE = 256
QR_MAX_SIZE = 1024
QR_MIN_SIZE = 64
# Per-cell QR size on the print sheet. Small enough that a 100-label sheet of
# inlined data: URIs stays a sane page weight, large enough to scan reliably.
QR_SHEET_CELL_SIZE = 180


def _qr_payload_for_item(stock_item_id: UUID) -> str:
    return f"{DORA_SCHEME_PREFIX}{stock_item_id}"


def _render_qr_png(payload: str, size: int) -> bytes:
    """qrcode picks a box_size that lets the matrix fit roughly inside the
    requested pixel size. We render then resize for a precise edge length
    so callers get the size they asked for."""
    # box_size of 10 is plenty of detail; border of 2 keeps the QR
    # scannable when surrounded by other ink.
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # PIL .resize uses LANCZOS for high-quality downscale; box-pixels look
    # crisp because the source is monochrome.
    from PIL import Image
    pil = img.convert("RGB")
    if pil.size != (size, size):
        pil = pil.resize((size, size), Image.NEAREST)
    buffer = io.BytesIO()
    pil.save(buffer, format="PNG")
    return buffer.getvalue()


def _parse_dora_link(value: str) -> UUID | None:
    """Returns the UUID inside a `dora://stock-item/<uuid>` URI, or None
    if `value` doesn't match that scheme.
    """
    if not value.startswith(DORA_SCHEME_PREFIX):
        return None
    candidate = value[len(DORA_SCHEME_PREFIX):].strip().strip("/")
    try:
        return UUID(candidate)
    except (ValueError, TypeError):
        return None


# ── GET /api/stock-items/<id>/qr ───────────────────────────────────────

@STOCK_ITEM_ROUTER.route("/<uuid:stock_item_id>/qr", methods=["GET"])
def stock_item_qr(stock_item_id: UUID):
    size_raw = request.args.get("size") or str(QR_DEFAULT_SIZE)
    try:
        size = int(size_raw)
    except ValueError:
        return bad_request("size must be an integer.")
    if size < QR_MIN_SIZE or size > QR_MAX_SIZE:
        return bad_request(
            f"size must be between {QR_MIN_SIZE} and {QR_MAX_SIZE} pixels."
        )
    repo = SqlAlchemyRepository()
    item = repo.get(StockItem).by_id(stock_item_id)
    if item is None:
        return not_found("StockItem", stock_item_id)
    png = _render_qr_png(_qr_payload_for_item(item.id), size)
    response = Response(png, mimetype="image/png")
    response.headers["Cache-Control"] = "private, max-age=300"
    return response


# ── GET /api/stock-items/qr/sheet?ids=...&layout=... ───────────────────

_SHEET_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>QR sheet · {{ layout.label }}</title>
  {{ css | safe }}
  <style>
    @page { size: {{ layout.page_size }}; margin: 8mm; }
    .grid {
      display: grid;
      grid-template-columns: repeat({{ layout.columns }}, 1fr);
      gap: 2mm;
      page-break-inside: auto;
    }
    .cell {
      width: {{ layout.cell_width_mm }}mm;
      height: {{ layout.cell_height_mm }}mm;
      padding: {{ layout.label_padding_mm }}mm;
      box-sizing: border-box;
      border: 1px dashed #ccc;
      display: flex;
      align-items: center;
      gap: 4mm;
      overflow: hidden;
      page-break-inside: avoid;
    }
    .cell img {
      width: {{ layout.cell_height_mm - 2 * layout.label_padding_mm }}mm;
      height: {{ layout.cell_height_mm - 2 * layout.label_padding_mm }}mm;
      flex-shrink: 0;
    }
    .cell .caption {
      font-size: 9pt;
      line-height: 1.2;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .cell .name { font-weight: 600; }
    .cell .level { color: #666; font-size: 8pt; }
    @media print { .cell { border-color: transparent; } }
  </style>
</head>
<body>
  {{ toolbar | safe }}
  <div class="page">
    <h1 style="font-size: 14pt;">QR sheet · {{ layout.label }}</h1>
    <div class="meta">{{ items | length }} label(s)</div>
    <div class="grid">
      {% for item in items %}
        <div class="cell">
          <img src="{{ item.qr_data_uri }}" alt="QR" />
          <div class="caption">
            <div class="name">{{ item.name }}</div>
            <div class="level">{{ item.level_name or '' }}</div>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""


@dataclass(slots=True)
class _SheetItem:
    id: UUID
    name: str
    level_name: str | None
    # The QR travels inside the HTML as a data: URI rather than as an
    # <img src="/api/..."> back-reference. The sheet is opened as a blob in
    # the SPA (so the fetch carries the session cookie the way every other
    # call does); a relative back-reference can't resolve from a blob origin,
    # and an absolute one would be an unauthenticated subresource. Self-
    # contained also means the page still prints correctly if it's saved.
    qr_data_uri: str


def _qr_data_uri(stock_item_id: UUID, size: int) -> str:
    png = _render_qr_png(_qr_payload_for_item(stock_item_id), size)
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def _iter_requested_ids(raw: str) -> Iterable[UUID]:
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            yield UUID(token)
        except (ValueError, TypeError):
            continue


@STOCK_ITEM_ROUTER.route("/qr/sheet", methods=["GET"])
def stock_item_qr_sheet():
    ids_raw = request.args.get("ids", "")
    layout_key = request.args.get("layout") or DEFAULT_LAYOUT_KEY
    layout = SHEET_LAYOUTS.get(layout_key)
    if layout is None:
        return bad_request(
            f"Unknown layout '{layout_key}'. Available: "
            f"{', '.join(SHEET_LAYOUTS.keys())}."
        )

    repo = SqlAlchemyRepository()
    requested = list(_iter_requested_ids(ids_raw))
    if not requested:
        # No ids → "print all stock items" shortcut from the brief.
        all_items = repo.get(StockItem).include("stock_level").all()
        items_for_sheet = [
            _SheetItem(
                id=i.id, name=i.name,
                level_name=i.stock_level.name if i.stock_level else None,
                qr_data_uri=_qr_data_uri(i.id, QR_SHEET_CELL_SIZE),
            )
            for i in sorted(all_items, key=lambda x: x.name.lower())
        ]
    else:
        items = (
            repo.get(StockItem)
            .include("stock_level")
            .all(EntityField(StockItem, "id").in_(requested))
        )
        by_id = {i.id: i for i in items}
        items_for_sheet = [
            _SheetItem(
                id=i.id, name=i.name,
                level_name=i.stock_level.name if i.stock_level else None,
                qr_data_uri=_qr_data_uri(i.id, QR_SHEET_CELL_SIZE),
            )
            # Honour the order the caller specified.
            for i in (by_id[rid] for rid in requested if rid in by_id)
        ]

    html = render_template_string(
        _SHEET_TEMPLATE,
        items=items_for_sheet,
        layout=layout,
        css=PRINT_CSS,
        toolbar=PRINT_TOOLBAR,
    )
    return Response(html, mimetype="text/html; charset=utf-8")


def _conflict(message: str) -> Response:
    """409-style response. The codebase has no `conflict` helper yet, so
    we cosplay one via unprocessable_entity with a 409 status override."""
    from http.client import CONFLICT
    response = unprocessable_entity(ProblemDetails(
        detail="See errors property for more details.",
        errors={"barcode": [message]},
        status=CONFLICT,
        title="Barcode already in use.",
        type="https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.8",
    ))
    response.status_code = CONFLICT
    return response


# ── GET /api/data/barcodes/lookup?value=... ────────────────────────────

@DATA_ROUTER.route("/barcodes/lookup", methods=["GET"])
def barcode_lookup():
    """Resolve a scanned value to one of four kinds (FU-056):

    * `stock_item`              — dora:// QR, or a `Barcode` row whose
                                   `stock_item_id` is set (direct registration
                                   wins as the most specific signal).
    * `stock_item_via_product`  — `Barcode` matches a Product that's linked
                                   to a StockItem via StockItemProduct.
                                   `StockItemProduct.UNIQUE(product_id)`
                                   guarantees at most one linked stock
                                   item.
    * `product_no_link`         — `Barcode` matches a Product the user has,
                                   but no linked StockItem.
    * `unknown`                 — nothing matched."""
    raw = (request.args.get("value") or "").strip()
    if not raw:
        return bad_request("value query parameter is required.")

    repo = SqlAlchemyRepository()

    # 1. dora:// link → stock_item
    parsed_uuid = _parse_dora_link(raw)
    if parsed_uuid is not None:
        item = repo.get(StockItem).by_id(parsed_uuid)
        if item is not None:
            return ok({"kind": "stock_item", "id": str(item.id)})
        return ok({"kind": "unknown", "value": raw})

    # 2. Real EAN — look up the Barcode row.
    match: Barcode | None = repo.get(Barcode).one(
        EntityField(Barcode, "barcode").eq(raw)
    )
    if match is None:
        return ok({"kind": "unknown", "value": raw})

    # Direct stock-item linkage wins (the user explicitly tied this barcode
    # to a specific pantry slot; honour their intent).
    if match.stock_item_id is not None:
        return ok({
            "kind": "stock_item",
            "id": str(match.stock_item_id),
            "barcode_id": str(match.id),
            "product_id": str(match.product_id) if match.product_id else None,
        })

    # Else traverse Product → linked stock item. `UNIQUE(product_id)`
    # on StockItemProduct (migration c4a8e2b9d7f5) guarantees at most
    # one linked row, so `.first()` is the natural shape — no caller
    # disambiguation needed.
    from sqlalchemy import select
    assoc = db.metadata.tables["StockItemProduct"]
    linked = db.session.execute(
        select(assoc.c.stock_item_id).where(assoc.c.product_id == match.product_id)
    ).first()
    if linked is not None:
        return ok({
            "kind": "stock_item_via_product",
            "id": str(linked[0]),
            "product_id": str(match.product_id),
            "barcode_id": str(match.id),
        })
    return ok({
        "kind": "product_no_link",
        "product_id": str(match.product_id),
        "barcode_id": str(match.id),
    })


# ── POST /api/data/barcodes ────────────────────────────────────────────

class RegisterBarcodeRequest(BaseModel):
    """Register a real-world EAN. Provide at least one of
    `product_id` or `stock_item_id`. Both is allowed (the user is saying
    the EAN is a Product's catalogue code *and* tied to their pantry slot).
    """
    model_config = ConfigDict(extra="forbid")
    barcode: str = Field(min_length=1, max_length=255)
    product_id: UUID | None = None
    stock_item_id: UUID | None = None

    @model_validator(mode="after")
    def _at_least_one_target(self) -> "RegisterBarcodeRequest":
        if self.product_id is None and self.stock_item_id is None:
            raise ValueError(
                "Provide product_id, stock_item_id, or both."
            )
        return self


@DATA_ROUTER.route("/barcodes", methods=["POST"])
@has_request_body(RegisterBarcodeRequest)
def register_barcode():
    _Logger = logging.getLogger(__name__)
    _Request: RegisterBarcodeRequest = get_request_body()
    raw = _Request.barcode.strip()
    if not raw:
        return bad_request("barcode cannot be blank.")

    repo = SqlAlchemyRepository()

    # Target entity existence checks — fail fast with clear messages.
    if _Request.product_id is not None:
        if repo.get(Product).by_id(_Request.product_id) is None:
            return not_found("Product", _Request.product_id)
    if _Request.stock_item_id is not None:
        if repo.get(StockItem).by_id(_Request.stock_item_id) is None:
            return not_found("StockItem", _Request.stock_item_id)

    # Pre-flight unique check on the barcode value (the DB UNIQUE constraint
    # is the real backstop, but this gives the caller a friendlier message).
    existing: Barcode | None = repo.get(Barcode).one(
        EntityField(Barcode, "barcode").eq(raw)
    )
    if existing is not None:
        return _conflict(f"Barcode '{raw}' is already registered.")

    row = Barcode(
        barcode=raw,
        product_id=_Request.product_id,
        stock_item_id=_Request.stock_item_id,
        created_at=datetime.now(timezone.utc),
    )
    repo.add(row)
    try:
        repo.save_changes()
    except IntegrityError as exc:
        repo.session.rollback()
        # Could be barcode-uniqueness (race) or product_id-uniqueness
        # (this Product already has a barcode). Inspect the message to
        # disambiguate; default to the broader "already in use".
        message = str(exc).lower()
        if "uq_barcode_product_id" in message or "product_id" in message:
            _Logger.warning("Per-product barcode unique conflict: %s", exc)
            return _conflict(
                "That product already has a barcode registered."
            )
        _Logger.warning("Barcode unique-constraint conflict: %s", exc)
        return _conflict(f"Barcode '{raw}' is already registered.")

    _Logger.info(
        "Registered barcode %s (product_id=%s, stock_item_id=%s)",
        raw, _Request.product_id, _Request.stock_item_id,
    )
    return ok({
        "barcode_id": str(row.id),
        "barcode": raw,
        "product_id": str(_Request.product_id) if _Request.product_id else None,
        "stock_item_id": str(_Request.stock_item_id) if _Request.stock_item_id else None,
    })


# ── DELETE /api/data/barcodes/<id> ─────────────────────────────────────

@DATA_ROUTER.route("/barcodes/<uuid:barcode_id>", methods=["DELETE"])
def delete_barcode(barcode_id: UUID):
    _Logger = logging.getLogger(__name__)
    repo = SqlAlchemyRepository()
    row = repo.get(Barcode).by_id(barcode_id)
    if row is None:
        return not_found("Barcode", barcode_id)
    repo.remove(row)
    repo.save_changes()
    _Logger.info("Deleted barcode %s (%s)", row.barcode, barcode_id)
    return no_content()
