"""`POST /api/ingest` — the producer-facing batch endpoint (C-10.2).

Auth: `Authorization: Bearer <key>` matched against `IngestionSource`.
The session-cookie middleware exempts this endpoint
(`middleware.PUBLIC_ENDPOINTS` carries `submit_ingestion_batch`); auth
lives here entirely.

Contract (PROPOSAL_INGESTION_API §2.2-§2.4):

- `Idempotency-Key` header: re-sending the same key under the same
  source is a no-op (last result is NOT cached — we just refuse to
  re-process to avoid double-writes).
- Payload: `{ products[], offers[] }`. Each record carries a `source`
  provenance string (defaults to the IngestionSource id if absent).
  **FU-227 chunk 7 (J1):** observations are in-app user input only;
  `price_observations[]` is no longer accepted (`extra="forbid"` rejects
  the field with a 400 — see PROPOSAL_PRODUCTS_AS_OVERLAY §2.5 "Idea A").
- Products dedupe on (store_id + stockcode) when stockcode is present,
  else (store_id + name) — same product across sources collapses into
  one row (shared catalogue, proposal §1/§5).
- Offers are append-only, deduped on
  (product_id, observed_at, price_now).
- FU-190: the producer's `store` string is resolved through
  `IngestionStoreMapping`. Unknown names quarantine (record skipped
  with `store_not_mapped`); admin maps later via the API access page.
  Stores are **never auto-created**.

Per-record results follow the seed-style DTO: a bad record never fails
the batch — `{ accepted: [...], skipped: [...], failed: [...] }`.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4

from flask import request
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.idempotency_key import IdempotencyKey
from dora_api.domain.entities.ingestion_source import IngestionSource
from dora_api.domain.entities.ingestion_store_mapping import \
    IngestionStoreMapping
from dora_api.domain.entities.store import Store
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.product_historic_offer import \
    ProductHistoricOffer
from dora_api.domain.entities.product_offer import ProductOffer
from dora_api.features.ingestion.offer_mapping import (OfferOutcome,
                                                       apply_offer_to_product)
from dora_api.features.routers import INGEST_ROUTER
from dora_api.infrastructure.api_response import unauthorized
from dora_api.infrastructure.ingestion_auth import (extract_bearer_token,
                                                    find_ingestion_source,
                                                    stamp_used)
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_Logger = logging.getLogger(__name__)

# Keys expire so the table stays bounded; long enough that an honest
# producer retrying a flaky network call still gets the no-op.
_IDEMPOTENCY_TTL = timedelta(days=7)


# ── Payload schema ─────────────────────────────────────────────────────

class _ProductIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    # FU-189 — producer pushes the store's external name as `store`. Was
    # `merchant` pre-Phase-E; the rename also flows through to the SPA
    # quarantine surface.
    store: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=255)
    size: str | None = Field(default=None, max_length=255)
    size_unit: str | None = Field(default=None, max_length=255)
    size_value: float | None = Field(default=None, gt=0)
    # `merchant_stockcode` carve-out: the producer's SKU code, kept
    # verbatim across the rename per the runbook.
    merchant_stockcode: str | None = Field(default=None, max_length=255)
    web_url: str | None = Field(default=None, max_length=500)
    source: str | None = Field(default=None, max_length=64)


class _OfferIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ref: str = Field(min_length=1, max_length=255)
    price_now: float = Field(gt=0)
    price_was: float | None = Field(default=None, gt=0)
    observed_at: datetime
    source: str | None = Field(default=None, max_length=64)


# FU-227 chunk 7 (J1) — `_PriceObservationIn` removed. Observations are an
# in-app user-input substrate only (PROPOSAL_PRODUCTS_AS_OVERLAY §2.5, Idea A):
# the producer never writes them. A request carrying `price_observations[]`
# is now rejected by `extra="forbid"` below; producers that wanted to push
# "I paid $X for product Y" should publish a one-point historic offer via
# the `offers[]` array instead — that's the offer/observation union point.


class IngestBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products: list[_ProductIn] = Field(default_factory=list)
    offers: list[_OfferIn] = Field(default_factory=list)


# ── Result DTOs ────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class _AcceptedRecord:
    kind: Literal["product", "offer"]
    ref: str
    id: str
    note: str | None = None  # e.g. "created" / "duplicate"


@dataclass(frozen=True, slots=True)
class _SkippedRecord:
    kind: Literal["product", "offer"]
    ref: str
    reason: str  # short stable code: duplicate, store_not_mapped, product_unknown, ...


@dataclass(frozen=True, slots=True)
class _FailedRecord:
    kind: Literal["product", "offer"]
    ref: str
    reason: str


@dataclass(slots=True)
class IngestBatchResult:
    accepted: list[_AcceptedRecord] = field(default_factory=list)
    skipped: list[_SkippedRecord] = field(default_factory=list)
    failed: list[_FailedRecord] = field(default_factory=list)
    idempotent_replay: bool = False


# ── Handler ────────────────────────────────────────────────────────────

class _IngestionContext:
    """Per-batch scratchpad: caches Store lookups, the products
    touched this batch (by ref), and the running result. Keeps the
    handler body tidy without piling on parameters."""

    def __init__(self, source: IngestionSource, repository: SqlAlchemyRepository) -> None:
        self.source = source
        self.repository = repository
        self.result = IngestBatchResult()
        # ref → Product, populated as products are upserted; offers in
        # the same batch can target newly-created products.
        self.products_by_ref: dict[str, Product] = {}
        # external store name → mapping row (resolved Store or None)
        self.store_cache: dict[str, IngestionStoreMapping] = {}


class SubmitIngestionBatchHandler:
    def __init__(self) -> None:
        self.repository = SqlAlchemyRepository()

    # — entrypoints —

    def handle(
        self,
        source: IngestionSource,
        idempotency_key: str | None,
        payload: IngestBatchRequest,
    ) -> IngestBatchResult:
        if idempotency_key and self._already_processed(source.id, idempotency_key):
            return IngestBatchResult(idempotent_replay=True)

        ctx = _IngestionContext(source, self.repository)

        for raw in payload.products:
            self._apply_product(ctx, raw)
        for raw in payload.offers:
            self._apply_offer(ctx, raw)
        # FU-227 chunk 7 — observations are in-app input only; the producer
        # path was removed (J1). Offer pushes still flow through above.

        # Counters land on the source row (consumed by C-10.3's
        # observability surface) — additive, so a re-send of a key
        # never double-counts.
        source.accepted_count += len(ctx.result.accepted)
        source.skipped_count += len(ctx.result.skipped)
        source.failed_count += len(ctx.result.failed)
        stamp_used(source)

        if idempotency_key:
            self._stamp_idempotency(source.id, idempotency_key)

        self.repository.save_changes()
        return ctx.result

    # — idempotency —

    def _already_processed(self, source_id: UUID, key: str) -> bool:
        field_key = EntityField(IdempotencyKey, IdempotencyKey.Fields.KEY)
        field_src = EntityField(IdempotencyKey, IdempotencyKey.Fields.SOURCE_ID)
        existing = self.repository.get(IdempotencyKey).one(
            field_key.eq(key) & field_src.eq(str(source_id))
        )
        if existing is None:
            return False
        # SQLite drops the tzinfo on roundtrip even when the column is
        # `DateTime(timezone=True)`; coerce a naive read to UTC so the
        # comparison is well-defined.
        expires = existing.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            # Expired — let it through, the new write will replace it.
            return False
        return True

    def _stamp_idempotency(self, source_id: UUID, key: str) -> None:
        row = IdempotencyKey(
            key=key,
            source_id=str(source_id),
            expires_at=datetime.now(timezone.utc) + _IDEMPOTENCY_TTL,
            created_at=datetime.now(timezone.utc),
        )
        self.repository.add(row)

    # — store mapping (FU-190) —

    def _resolve_store(
        self, ctx: _IngestionContext, external_name: str
    ) -> tuple[Store | None, IngestionStoreMapping]:
        """Look up (or create-as-quarantined) the per-source store
        mapping; return the Dora Store if mapped, else None."""
        cached = ctx.store_cache.get(external_name)
        if cached is not None:
            mapping = cached
        else:
            field_src = EntityField(
                IngestionStoreMapping, IngestionStoreMapping.Fields.SOURCE_ID
            )
            field_ext = EntityField(
                IngestionStoreMapping, IngestionStoreMapping.Fields.EXTERNAL_NAME
            )
            mapping = self.repository.get(IngestionStoreMapping).one(
                field_src.eq(ctx.source.id) & field_ext.eq(external_name)
            )
            if mapping is None:
                # First sighting — create the quarantined row so the
                # admin sees a pending mapping to resolve. Stores are
                # never auto-created.
                mapping = IngestionStoreMapping(
                    source_id=ctx.source.id,
                    external_name=external_name,
                    store_id=None,
                    created_at=datetime.now(timezone.utc),
                    last_seen_at=datetime.now(timezone.utc),
                )
                self.repository.add(mapping)
            ctx.store_cache[external_name] = mapping

        mapping.last_seen_at = datetime.now(timezone.utc)
        if mapping.store_id is None:
            return None, mapping
        store = self.repository.get(Store).by_id(mapping.store_id)
        return store, mapping

    # — record applicators —

    def _apply_product(self, ctx: _IngestionContext, raw: _ProductIn) -> None:
        store, _mapping = self._resolve_store(ctx, raw.store)
        if store is None:
            ctx.result.skipped.append(_SkippedRecord(
                kind="product", ref=raw.ref, reason="store_not_mapped",
            ))
            return

        # Dedupe: stockcode-first, name fallback. Source is provenance
        # only, NOT identity — same product pushed by two sources
        # collapses into one Product row (shared catalogue).
        field_name = EntityField(Product, Product.Fields.NAME)
        field_stockcode = EntityField(Product, Product.Fields.MERCHANT_STOCKCODE)
        field_store_id = EntityField(Store, Store.Fields.ID)

        existing: Product | None = None
        if raw.merchant_stockcode:
            existing = (
                self.repository.get(Product)
                .include(Product.Fields.STORE)
                .include(Product.Fields.CURRENT_OFFER)
                .one(
                    field_stockcode.eq(raw.merchant_stockcode)
                    & field_store_id.eq(store.id)
                )
            )
        if existing is None:
            existing = (
                self.repository.get(Product)
                .include(Product.Fields.STORE)
                .include(Product.Fields.CURRENT_OFFER)
                .one(field_name.eq(raw.name) & field_store_id.eq(store.id))
            )

        record_source = raw.source or str(ctx.source.id)

        if existing is not None:
            # Refresh mutable attributes; provenance recorded via the
            # next offer push, not the product row itself.
            existing.brand = raw.brand or existing.brand
            existing.size = raw.size or existing.size
            existing.size_unit = raw.size_unit or existing.size_unit
            existing.size_value = raw.size_value or existing.size_value
            existing.web_url = raw.web_url or existing.web_url
            existing.is_active = True
            ctx.products_by_ref[raw.ref] = existing
            ctx.result.accepted.append(_AcceptedRecord(
                kind="product", ref=raw.ref, id=str(existing.id), note="updated",
            ))
            return

        # Create — initial offer mirrors the not-yet-known price; the
        # next /ingest offer for this product moves it. v1 producers
        # always push an offer for the same product so this is fine.
        initial_offer = ProductOffer(
            offered_on=datetime.now(timezone.utc),
            price_now=0.0,
            price_was=0.0,
        )
        product = Product(
            brand=raw.brand,
            current_offer=initial_offer,
            historic_offers=[],
            image=None,
            is_active=True,
            is_available=True,
            store=store,
            merchant_stockcode=raw.merchant_stockcode,
            name=raw.name,
            size=raw.size or "",
            size_unit=raw.size_unit or "",
            size_value=raw.size_value or 0.0,
            web_url=raw.web_url,
        )
        self.repository.add(initial_offer)
        self.repository.add(product)
        ctx.products_by_ref[raw.ref] = product
        ctx.result.accepted.append(_AcceptedRecord(
            kind="product", ref=raw.ref, id=str(product.id),
            note=f"created (provenance: {record_source})",
        ))

    def _apply_offer(self, ctx: _IngestionContext, raw: _OfferIn) -> None:
        product = ctx.products_by_ref.get(raw.product_ref)
        if product is None:
            ctx.result.failed.append(_FailedRecord(
                kind="offer", ref=raw.product_ref, reason="product_unknown",
            ))
            return

        record_source = raw.source or str(ctx.source.id)
        outcome = apply_offer_to_product(
            self.repository,
            product,
            price_now=raw.price_now,
            price_was=raw.price_was,
            observed_at=raw.observed_at,
            source=record_source,
        )
        if outcome.outcome == OfferOutcome.DUPLICATE:
            ctx.result.skipped.append(_SkippedRecord(
                kind="offer", ref=raw.product_ref, reason="duplicate",
            ))
            return
        ctx.result.accepted.append(_AcceptedRecord(
            kind="offer", ref=raw.product_ref,
            id=outcome.historic_offer_id or "",
            note="appended",
        ))

# FU-227 chunk 7 (J1) — `_apply_observation` removed. The producer no longer
# writes observations; users do, via the in-app PriceEntry widget. The
# product-anchored half of the old method (push a single-point historic offer
# from a "$X for product Y" payload) was always a misuse of the observation
# substrate — that intent is properly expressed by a row in `offers[]` with
# the same `observed_at` + `price_now`, which the `_apply_offer` path above
# already covers.


# ── Route ──────────────────────────────────────────────────────────────


@INGEST_ROUTER.route("", methods=["POST"], endpoint="submit_ingestion_batch")
def submit_ingestion_batch():
    raw_token = extract_bearer_token()
    source = find_ingestion_source(raw_token) if raw_token else None
    if source is None:
        return unauthorized("Bearer token missing or invalid.")

    try:
        payload = IngestBatchRequest.model_validate(request.get_json(silent=True) or {})
    except Exception as exc:  # noqa: BLE001 — pydantic validation surface
        return ({"detail": "Malformed payload.", "errors": str(exc)}, 400)

    idempotency_key = (request.headers.get("Idempotency-Key") or "").strip() or None

    handler = SubmitIngestionBatchHandler()
    result = handler.handle(source, idempotency_key, payload)

    _Logger.info(
        "Ingest batch from source %s: %d accepted, %d skipped, %d failed%s",
        source.id, len(result.accepted), len(result.skipped),
        len(result.failed), " (replay)" if result.idempotent_replay else "",
    )
    return {
        "accepted": [asdict(r) for r in result.accepted],
        "skipped": [asdict(r) for r in result.skipped],
        "failed": [asdict(r) for r in result.failed],
        "idempotent_replay": result.idempotent_replay,
    }
