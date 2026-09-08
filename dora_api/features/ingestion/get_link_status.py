"""`POST /api/ingest/link-status` — C-10.5, FU-422.

Read-side companion to `POST /api/ingest`. An ingestion source (companion or
any other) passes a batch of product identifiers using the SAME shape it
would push to `/api/ingest` — `(store, merchant_stockcode)` first, falling
back to `(store, name)` — and gets back, per item, whether Dora already
holds that product and, if so, whether it's linked to a stock item. Lets the
caller decorate its own search UI with "already linked" so the user doesn't
re-link a product Dora already has bound (original spec intent — the FU
that motivated this doc-anchored the answer here rather than in Dora's UI,
since Dora has no in-app product-search surface).

Contract:
- Auth: `Authorization: Bearer <key>` matched against `IngestionSource` —
  same helpers as the batch endpoint, same middleware exemption.
- Request: `{ items: [{ ref, store, merchant_stockcode?, name? }] }`.
  Each item must supply at least one of `merchant_stockcode`/`name` (mirrors
  `_ProductIn` identity in `submit_ingestion_batch`).
- Response: `{ items: [{ ref, product_id, linked_stock_item_id,
  linked_stock_item_name, reason? }] }`. `product_id` is null when Dora
  doesn't hold the product (or the store isn't mapped for this source);
  `linked_*` are null when the product exists but isn't bound to a stock
  item. `reason` is a stable short code when nothing was resolved
  (`store_not_mapped`, `product_not_found`).
- Source-agnostic: nothing in the response references the caller (R-005
  invisibility). The store-mapping lookup is per-source only because that's
  how the write side resolves the same name → Store — read must match write.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from uuid import UUID

from flask import request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.ingestion_source import IngestionSource
from dora_api.domain.entities.ingestion_store_mapping import \
    IngestionStoreMapping
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.store import Store
from dora_api.features.routers import INGEST_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.ingestion_auth import (
    authenticate_ingestion_request, stamp_used)
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_Logger = logging.getLogger(__name__)

# Caps the per-call fan-out. A companion decorating a search-results page
# rarely wants more than a few dozen; the ceiling keeps a bad caller from
# turning this into an accidental catalogue dump.
_MAX_ITEMS = 200


class _LookupItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str = Field(min_length=1, max_length=255)
    store: str = Field(min_length=1, max_length=255)
    merchant_stockcode: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=255)


class _LinkStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[_LookupItem] = Field(default_factory=list, max_length=_MAX_ITEMS)


@dataclass(frozen=True, slots=True)
class _LinkStatusResult:
    ref: str
    product_id: str | None
    linked_stock_item_id: str | None
    linked_stock_item_name: str | None
    reason: str | None = None


class GetLinkStatusHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(
        self,
        source: IngestionSource,
        payload: _LinkStatusRequest,
    ) -> list[_LinkStatusResult]:
        results: list[_LinkStatusResult] = []
        # Per-source store name → Store.id (or None if quarantined). Cache
        # inside the call so a batch of 50 items for the same external
        # store is one lookup, not 50.
        store_cache: dict[str, UUID | None] = {}
        # (store_id, product_id) accumulator for the join lookup below.
        resolved: list[tuple[int, Product]] = []

        for idx, item in enumerate(payload.items):
            if not item.merchant_stockcode and not item.name:
                results.append(_LinkStatusResult(
                    ref=item.ref, product_id=None,
                    linked_stock_item_id=None, linked_stock_item_name=None,
                    reason="product_not_found",
                ))
                continue

            store_id = self._resolve_store_id(source, item.store, store_cache)
            if store_id is None:
                results.append(_LinkStatusResult(
                    ref=item.ref, product_id=None,
                    linked_stock_item_id=None, linked_stock_item_name=None,
                    reason="store_not_mapped",
                ))
                continue

            product = self._find_product(store_id, item.merchant_stockcode, item.name)
            if product is None:
                results.append(_LinkStatusResult(
                    ref=item.ref, product_id=None,
                    linked_stock_item_id=None, linked_stock_item_name=None,
                    reason="product_not_found",
                ))
                continue

            # Slot filled in the second pass so we can do one bulk join.
            results.append(_LinkStatusResult(
                ref=item.ref, product_id=str(product.id),
                linked_stock_item_id=None, linked_stock_item_name=None,
            ))
            resolved.append((idx, product))

        self._stamp_linked_stock_items(results, resolved)
        return results

    def _resolve_store_id(
        self,
        source: IngestionSource,
        external_name: str,
        cache: dict[str, UUID | None],
    ) -> UUID | None:
        """Per-source external name → Store.id, mirroring
        `SubmitIngestionBatchHandler._resolve_store` but read-only:
        unresolved names are NOT quarantined here (a lookup is not an
        ingest event; quarantine belongs to the write side)."""
        if external_name in cache:
            return cache[external_name]

        field_src = EntityField(
            IngestionStoreMapping, IngestionStoreMapping.Fields.SOURCE_ID
        )
        field_ext = EntityField(
            IngestionStoreMapping, IngestionStoreMapping.Fields.EXTERNAL_NAME
        )
        mapping = self.repository.get(IngestionStoreMapping).one(
            field_src.eq(source.id) & field_ext.eq(external_name)
        )
        store_id = mapping.store_id if mapping and mapping.store_id else None
        cache[external_name] = store_id
        return store_id

    def _find_product(
        self,
        store_id: UUID,
        stockcode: str | None,
        name: str | None,
    ) -> Product | None:
        """Stockcode-first, name fallback — same order the write side uses,
        so a caller that pushes with stockcode gets a symmetric lookup."""
        field_name = EntityField(Product, Product.Fields.NAME)
        field_stockcode = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)
        field_store_id = EntityField(Store, Store.Fields.ID)

        if stockcode:
            existing = self.repository.get(Product).one(
                field_stockcode.eq(stockcode) & field_store_id.eq(store_id)
            )
            if existing is not None:
                return existing
        if name:
            return self.repository.get(Product).one(
                field_name.eq(name) & field_store_id.eq(store_id)
            )
        return None

    def _stamp_linked_stock_items(
        self,
        results: list[_LinkStatusResult],
        resolved: list[tuple[int, Product]],
    ) -> None:
        """One bulk pass over the StockItemProduct join, then a single
        StockItem lookup for the names. Mirrors the shape of
        `products.get_products.stamp_linked_stock_items` — same table, same
        (product → stock-item) mapping. Not called through the shared
        helper because that one mutates ProductDto objects; the shape here
        is a `_LinkStatusResult` dataclass."""
        if not resolved:
            return
        product_ids = [p.id for _, p in resolved]
        assoc = db.metadata.tables["StockItemProduct"]
        rows = self.repository.session.execute(
            select(assoc.c.product_id, assoc.c.stock_item_id)
            .where(assoc.c.product_id.in_(product_ids))
        ).all()
        product_to_stock: dict[UUID, UUID] = {row[0]: row[1] for row in rows}
        stock_ids = list({sid for sid in product_to_stock.values()})
        stock_lookup: dict[UUID, StockItem] = {}
        if stock_ids:
            items = self.repository.get(StockItem).all(
                EntityField(StockItem, "id").in_(stock_ids)
            )
            stock_lookup = {s.id: s for s in items}

        for idx, product in resolved:
            stock_id = product_to_stock.get(product.id)
            if stock_id is None:
                continue
            item = stock_lookup.get(stock_id)
            results[idx] = _LinkStatusResult(
                ref=results[idx].ref,
                product_id=results[idx].product_id,
                linked_stock_item_id=str(stock_id),
                linked_stock_item_name=item.name if item else None,
            )


@INGEST_ROUTER.route("/link-status", methods=["POST"], endpoint="ingest_link_status")
def ingest_link_status():
    # FU-866 — one shared check: authenticate, then honour the
    # install-wide ingestion switch. Both live in `ingestion_auth` so a
    # new ingest route cannot quietly skip the gate.
    source, auth_error = authenticate_ingestion_request()
    if auth_error is not None:
        return auth_error

    try:
        payload = _LinkStatusRequest.model_validate(request.get_json(silent=True) or {})
    except Exception as exc:  # noqa: BLE001 — pydantic surface, mirrors submit_ingestion_batch
        return ({"detail": "Malformed payload.", "errors": str(exc)}, 400)

    repository = SqlAlchemyRepository()
    results = GetLinkStatusHandler(repository).handle(source, payload)
    stamp_used(source)
    repository.save_changes()

    _Logger.info(
        "Link-status lookup from source %s: %d items, %d matched",
        source.id, len(results),
        sum(1 for r in results if r.product_id is not None),
    )
    return ok({"items": [asdict(r) for r in results]})
