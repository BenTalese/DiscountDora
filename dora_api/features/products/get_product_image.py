"""FU-014 — product image route.

  GET /api/products/<id>/image

Returns the product's stored image as raw bytes with the correct mimetype.
Images are stored as data-URL strings on the entity
(`data:image/jpeg;base64,...`) so the SPA can use a plain `<img src>` against
this route without inlining megabytes of base64 in every list/detail JSON.
Same pattern as the stock-item-image and recipe-image routes.
"""
import base64
import re

from flask import Response

from dora_api.domain.entities.product import Product
from dora_api.features.routers import PRODUCT_ROUTER
from dora_api.infrastructure.api_response import not_found
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_DATA_URL_RE = re.compile(r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$", re.DOTALL)


def _decode_data_url(blob: bytes | None) -> tuple[str, bytes] | None:
    if not blob:
        return None
    data_url = blob.decode("utf-8", "ignore")
    match = _DATA_URL_RE.match(data_url)
    if not match:
        return None
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, TypeError):
        return None
    return match.group("mime"), raw


@PRODUCT_ROUTER.route("/<product_id>/image", methods=["GET"])
def get_product_image(product_id):
    repository = SqlAlchemyRepository()
    product = repository.get(Product).by_id(product_id)
    if product is None:
        return not_found(Product.__name__, product_id)

    decoded = _decode_data_url(getattr(product, "image", None))
    if decoded is None:
        return not_found(Product.__name__, product_id)

    mime, raw = decoded
    return Response(
        raw,
        mimetype=mime,
        headers={"Cache-Control": "no-cache"},
    )
