"""Admin CRUD over `IngestionStoreMapping` (C-10.2 / FU-190).

The API access page lists pending (`merchant_id IS NULL`) and resolved
mappings per source. The admin assigns or clears the Dora `Merchant`
each external name resolves to. Stores are **never auto-created** here
either — the admin picks one of the existing Merchants.

Endpoints (all admin-only, session-cookie):

- `GET /api/ingestion-sources/<source_id>/store-mappings`         — list
- `PUT /api/ingestion-sources/<source_id>/store-mappings`         — upsert
- `DELETE /api/ingestion-sources/<source_id>/store-mappings/<id>` — drop
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.ingestion_source import IngestionSource
from dora_api.domain.entities.ingestion_store_mapping import \
    IngestionStoreMapping
from dora_api.domain.entities.merchant import Merchant
from dora_api.features.ingestion_sources.ingestion_source_admin import \
    _require_admin
from dora_api.features.routers import INGESTION_SOURCE_ROUTER
from dora_api.infrastructure.api_response import (bad_request, no_content,
                                                  not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class StoreMappingDto:
    id: UUID
    source_id: UUID
    external_name: str
    merchant_id: UUID | None
    merchant_name: str | None
    created_at: datetime
    last_seen_at: datetime | None

    @classmethod
    def from_entity(
        cls, mapping: IngestionStoreMapping, merchant: Merchant | None
    ) -> "StoreMappingDto":
        return cls(
            id=mapping.id,
            source_id=mapping.source_id,
            external_name=mapping.external_name,
            merchant_id=mapping.merchant_id,
            merchant_name=merchant.name if merchant else None,
            created_at=mapping.created_at,
            last_seen_at=mapping.last_seen_at,
        )


class UpsertStoreMappingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_name: str = Field(min_length=1, max_length=255)
    # `null` to quarantine (clears the link); a UUID to bind.
    merchant_id: UUID | None = None


class ListStoreMappingsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, source_id: UUID) -> list[StoreMappingDto] | None:
        if self.repository.get(IngestionSource).by_id(source_id) is None:
            return None
        field_src = EntityField(
            IngestionStoreMapping, IngestionStoreMapping.Fields.SOURCE_ID
        )
        rows: list[IngestionStoreMapping] = (
            self.repository.get(IngestionStoreMapping)
            .all(field_src.eq(source_id))
        )
        rows.sort(key=lambda r: (r.merchant_id is not None, r.external_name))
        merchant_ids = {r.merchant_id for r in rows if r.merchant_id is not None}
        merchants_by_id: dict[UUID, Merchant] = {}
        for mid in merchant_ids:
            m = self.repository.get(Merchant).by_id(mid)
            if m is not None:
                merchants_by_id[mid] = m
        return [
            StoreMappingDto.from_entity(
                r, merchants_by_id.get(r.merchant_id) if r.merchant_id else None
            )
            for r in rows
        ]


class UpsertStoreMappingHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self, source_id: UUID, req: UpsertStoreMappingRequest
    ) -> tuple[StoreMappingDto | None, str | None]:
        if self.repository.get(IngestionSource).by_id(source_id) is None:
            return None, "source_not_found"

        merchant: Merchant | None = None
        if req.merchant_id is not None:
            merchant = self.repository.get(Merchant).by_id(req.merchant_id)
            if merchant is None:
                return None, "merchant_not_found"

        field_src = EntityField(
            IngestionStoreMapping, IngestionStoreMapping.Fields.SOURCE_ID
        )
        field_ext = EntityField(
            IngestionStoreMapping, IngestionStoreMapping.Fields.EXTERNAL_NAME
        )
        existing: IngestionStoreMapping | None = (
            self.repository.get(IngestionStoreMapping)
            .one(field_src.eq(source_id) & field_ext.eq(req.external_name))
        )
        if existing is None:
            mapping = IngestionStoreMapping(
                source_id=source_id,
                external_name=req.external_name,
                merchant_id=req.merchant_id,
                created_at=datetime.now(timezone.utc),
                last_seen_at=None,
            )
            self.repository.add(mapping)
        else:
            existing.merchant_id = req.merchant_id
            mapping = existing
        self.repository.save_changes()
        return StoreMappingDto.from_entity(mapping, merchant), None


class DeleteStoreMappingHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, source_id: UUID, mapping_id: UUID) -> bool:
        field_src = EntityField(
            IngestionStoreMapping, IngestionStoreMapping.Fields.SOURCE_ID
        )
        target: IngestionStoreMapping | None = (
            self.repository.get(IngestionStoreMapping)
            .one(EntityField(IngestionStoreMapping, "id").eq(mapping_id)
                 & field_src.eq(source_id))
        )
        if target is None:
            return False
        self.repository.remove(target)
        self.repository.save_changes()
        return True


# ── Routes ─────────────────────────────────────────────────────────────


@INGESTION_SOURCE_ROUTER.route("<source_id>/store-mappings", methods=["GET"])
def list_store_mappings(source_id: UUID):
    _, err = _require_admin()
    if err is not None:
        return err
    items = get_container().inject(ListStoreMappingsHandler).handle(source_id)
    if items is None:
        return not_found("IngestionSource", source_id)
    return {"items": [asdict(it) for it in items]}


@INGESTION_SOURCE_ROUTER.route("<source_id>/store-mappings", methods=["PUT"])
@has_request_body(UpsertStoreMappingRequest)
def upsert_store_mapping(source_id: UUID):
    _, err = _require_admin()
    if err is not None:
        return err
    req: UpsertStoreMappingRequest = get_request_body()
    result, error = get_container().inject(UpsertStoreMappingHandler).handle(source_id, req)
    if error == "source_not_found":
        return not_found("IngestionSource", source_id)
    if error == "merchant_not_found":
        return bad_request("merchant_id does not match any existing Merchant.")
    logging.getLogger(__name__).info(
        "Upserted store mapping %s for source %s (external=%s, merchant=%s)",
        result.id, source_id, result.external_name, result.merchant_id,
    )
    return asdict(result)


@INGESTION_SOURCE_ROUTER.route(
    "<source_id>/store-mappings/<mapping_id>", methods=["DELETE"]
)
def delete_store_mapping(source_id: UUID, mapping_id: UUID):
    _, err = _require_admin()
    if err is not None:
        return err
    ok = get_container().inject(DeleteStoreMappingHandler).handle(source_id, mapping_id)
    if not ok:
        return not_found("IngestionStoreMapping", mapping_id)
    return no_content()
