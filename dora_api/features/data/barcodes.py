"""Barcode + QR endpoints.

  GET    /api/stock-items/<id>/qr                       — PNG of the item's dora:// QR
  GET    /api/stock-items/qr/sheet                      — HTML print-sheet of many QRs
  GET    /api/barcodes/lookup?value=...                 — disambiguate a scanned value
  POST   /api/barcodes/register-against-product         — link a real barcode to a Product

QR generation uses `qrcode[pil]` (pure Python + Pillow). The sheet
endpoint is HTML so the user can print or Save-as-PDF — consistent
with the no-server-PDF call we made in N4.

Model note (P6-02): a real-world barcode (EAN/UPC) identifies a *Product*, not
a stock item, so it lives in `ProductBarcode`. There is deliberately no
`StockItem.barcode` — lookup resolves a real barcode to its Product, then to a
linked stock item. Scanning is a navigation aid only; it never does live deal
lookup.
"""
import io
import logging
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse
from uuid import UUID

import qrcode
from flask import Response, render_template_string, request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_barcode import ProductBarcode
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.data.export_shared import PRINT_CSS, PRINT_TOOLBAR
from dora_api.features.routers import (
    DATA_ROUTER, STOCK_ITEM_ROUTER,
)
from dora_api.infrastructure.api_response import (
    bad_request, not_found, ok,
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

@STOCK_ITEM_ROUTER.route("/<stock_item_id>/qr", methods=["GET"])
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
          <img src="/api/stock-items/{{ item.id }}/qr?size=180" alt="QR" />
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


# ── GET /api/barcodes/lookup?value=... ─────────────────────────────────

@DATA_ROUTER.route("/barcodes/lookup", methods=["GET"])
def barcode_lookup():
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

    # 2. ProductBarcode hit → resolve linked stock item (if any). Real-world
    #    barcodes identify a Product, never a stock item directly.
    product_match: ProductBarcode | None = repo.get(ProductBarcode).one(
        EntityField(ProductBarcode, "barcode").eq(raw)
    )
    if product_match is not None:
        # Any stock item with this product in its m2m. The repository doesn't
        # expose secondary-table queries cleanly, so we touch SQLAlchemy
        # directly for the lookup.
        from sqlalchemy import select
        from dora_api.app import db
        assoc = db.metadata.tables["StockItemProduct"]
        row = db.session.execute(
            select(assoc.c.stock_item_id).where(assoc.c.product_id == product_match.product_id)
        ).first()
        linked_stock_item_id = str(row[0]) if row else None

        return ok({
            "kind": "product",
            "id": str(product_match.product_id),
            "stock_item_id": linked_stock_item_id,
        })

    return ok({"kind": "unknown", "value": raw})


# ── POST /api/barcodes/register-against-product ────────────────────────

class RegisterProductBarcodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: UUID
    barcode: str = Field(min_length=1, max_length=255)


@DATA_ROUTER.route("/barcodes/register-against-product", methods=["POST"])
@has_request_body(RegisterProductBarcodeRequest)
def register_product_barcode():
    _Logger = logging.getLogger(__name__)
    _Request: RegisterProductBarcodeRequest = get_request_body()
    barcode = _Request.barcode.strip()
    if not barcode:
        return bad_request("barcode cannot be blank.")

    repo = SqlAlchemyRepository()
    product = repo.get(Product).by_id(_Request.product_id)
    if product is None:
        return not_found("Product", _Request.product_id)

    existing: ProductBarcode | None = repo.get(ProductBarcode).one(
        EntityField(ProductBarcode, "barcode").eq(barcode)
    )
    if existing is not None:
        return _conflict(
            f"Barcode '{barcode}' is already registered against another product."
        )

    row = ProductBarcode(product_id=product.id, barcode=barcode)
    repo.add(row)
    try:
        repo.save_changes()
    except IntegrityError as exc:
        repo.session.rollback()
        _Logger.warning("Product barcode unique-constraint conflict: %s", exc)
        return _conflict(f"Barcode '{barcode}' is already in use.")

    _Logger.info(
        "Registered barcode %s against product %s", barcode, _Request.product_id,
    )
    return ok({
        "product_barcode_id": str(row.id),
        "product_id": str(product.id),
        "barcode": barcode,
    })
