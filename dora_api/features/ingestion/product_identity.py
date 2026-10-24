"""Product identity for the ingestion seam — one lookup, both directions.

Both halves of `/api/ingest` answer the same question, "which `Product` row
is this `(store, merchant_stockcode | name)`?": the write side
(`submit_ingestion_batch._apply_product`) to dedupe an incoming record onto
an existing row, the read side (`get_link_status._find_product`) to tell a
producer what Dora already holds so it can decorate its own search results
and offer *unsave*.

They used to carry two copies of the lookup, and the copies disagreed on
OD-2 (hand-entered "custom" products are the user's own and are never
adopted by machinery): the write side skipped `is_custom` rows, the read
side did not. So a search for a name the user had typed in by hand came
back "already in Dora", and the companion's unsave then deleted the user's
own product through `DELETE /api/ingest/products/<id>` (finalisation
16-R8). This module is the single answer (R-003); `find_ingested_product`
is the only place the stockcode-first / name-fallback / never-custom rule
is written.
"""
from __future__ import annotations

from uuid import UUID

from dora_api.domain.entities.product import Product
from dora_api.domain.entities.store import Store
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField


def find_ingested_product(
    repository: Repository,
    store_id: UUID,
    stockcode: str | None,
    name: str | None,
    *,
    includes: tuple[str, ...] = (),
) -> Product | None:
    """The ingested (never custom) product at `store_id` matching
    `stockcode` first, then `name`.

    `includes` are relationship names to eager-load (`Product.Fields.STORE`,
    `Product.Fields.CURRENT_OFFER`) for callers that go on to mutate the row;
    a read-only caller passes none.
    """
    field_name = EntityField(Product, Product.Fields.NAME)
    field_stockcode = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)
    field_store_id = EntityField(Store, Store.Fields.ID)
    # OD-2 — a custom product is the user's to edit. A scraped record with
    # the same name at the same store creates its own row rather than
    # overwriting the user's figure, and a lookup must say "not held" so a
    # producer never learns a custom product's id.
    not_custom = EntityField(Product, Product.Fields.IS_CUSTOM).eq(False)

    def _query():
        query = repository.get(Product)
        for relationship in includes:
            query = query.include(relationship)
        return query

    if stockcode:
        existing = _query().one(
            field_stockcode.eq(stockcode) & field_store_id.eq(store_id) & not_custom
        )
        if existing is not None:
            return existing
    if name:
        return _query().one(
            field_name.eq(name) & field_store_id.eq(store_id) & not_custom
        )
    return None
