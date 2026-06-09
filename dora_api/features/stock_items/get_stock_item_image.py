"""C-1 Chunk 6 / FU-033 — stock-item image route + product fallback.

  GET /api/stock-items/<id>/image

Resolution order (matches the original spec quoted in FU-033):
  1. The stock item's own `image` blob (data-URL bytes), if present.
  2. The image of any linked Product, if a linked product carries one.
  3. 404.

Images are stored as data-URL strings on the entity (`data:image/png;
base64,…`) so the SPA can use a plain `<img src>` against this route
without inlining megabytes of base64 in every list/detail JSON. Same
pattern as the recipe-image route added in Cookbook Chunk 5.
"""
import base64
import logging
import re

from flask import Response

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import not_found
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_DATA_URL_RE = re.compile(r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$", re.DOTALL)


def _decode_data_url(blob: bytes | None) -> tuple[str, bytes] | None:
    """Return `(mime, raw_bytes)` from a stored data-URL blob, or None when
    the blob is empty or malformed. Empty / malformed → caller treats as
    "no image" and falls through to the next resolution step."""
    if not blob:
        return None
    try:
        data_url = blob.decode("utf-8", "ignore")
    except Exception:  # pragma: no cover — bytes.decode("utf-8", "ignore") doesn't raise
        return None
    match = _DATA_URL_RE.match(data_url)
    if not match:
        return None
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, TypeError):
        return None
    return match.group("mime"), raw


@STOCK_ITEM_ROUTER.route("/<stock_item_id>/image", methods=["GET"])
def get_stock_item_image(stock_item_id):
    """Resolve the stock item's image with linked-product fallback."""
    repository = SqlAlchemyRepository()
    # `products` is mapped `lazy="noload"`; include it explicitly so the
    # fallback path can scan linked products without a second round trip.
    item = (
        repository
        .get(StockItem)
        .include(StockItem.Fields.PRODUCTS)
        .by_id(stock_item_id)
    )
    if item is None:
        return not_found(StockItem.__name__, stock_item_id)

    decoded = _decode_data_url(getattr(item, "image", None))
    if decoded is None:
        # Fall back to a linked product's image. There may be several;
        # take the first that decodes cleanly so a malformed one doesn't
        # mask a usable sibling.
        for product in (item.products or []):
            decoded = _decode_data_url(getattr(product, "image", None))
            if decoded is not None:
                logging.getLogger(__name__).debug(
                    "stock item %s using fallback image from product %s",
                    stock_item_id, product.id,
                )
                break

    if decoded is None:
        return not_found(StockItem.__name__, stock_item_id)

    mime, raw = decoded
    return Response(
        raw,
        mimetype=mime,
        headers={"Cache-Control": "no-cache"},
    )
