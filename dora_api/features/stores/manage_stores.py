"""FU-189 — Store CRUD (replaces the legacy `features/merchants/get_merchants`).

Stores are user-curated. Dora ships **zero pre-seeded stores** (no
locale-coupling, no logo-licensing risk) and the manual creator never
auto-creates a row outside this module — the dedicated POST is the only
public creation path. Ingestion auto-create remains separately gated by
FU-190.

Per-store image upload reuses the C-cross §2.8 data-URL convention used by
stock items / products / recipes: a `data:image/...;base64,...` UTF-8 blob
on the entity, served back via `GET /stores/<id>/image`.

Endpoints:

  GET    /api/stores               — list all stores (with usage counts)
  POST   /api/stores               — create
  PATCH  /api/stores/<id>          — rename / replace image
  DELETE /api/stores/<id>          — delete (linked stock items/lines fall
                                     to NULL via the FK's ON DELETE SET NULL;
                                     Product.store_id is RESTRICT — products
                                     must be detached first)
  GET    /api/stores/<id>/image    — raw image bytes
"""
import base64
import logging
import re
from dataclasses import dataclass
from typing import List
from uuid import UUID

from flask import Response, request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.shopping_list import ShoppingListLine
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.store import Store
from dora_api.features.routers import STORE_ROUTER
from dora_api.infrastructure.api_response import (bad_request,
                                                  business_rule_violation,
                                                  created, no_content,
                                                  not_found, ok, paginated)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ───── DTOs ─────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class StoreDto:
    store_id: UUID
    name: str
    # bytes never travel in list/detail JSON. SPA fetches via
    # `GET /stores/<id>/image`.
    has_image: bool

    @classmethod
    def from_entity(cls, store: Store) -> 'StoreDto':
        # `has_image` is stamped in bulk to avoid triggering the deferred
        # image-blob load per row.
        return StoreDto(
            store_id = store.id,
            name = store.name,
            has_image = False,
        )


_FIELD_MAP: dict[str, EntityField] = {
    "store_id": EntityField(Store, "id"),
}


def _stamp_has_image(repository, dtos: List[StoreDto]) -> None:
    if not dtos:
        return
    store_ids = [d.store_id for d in dtos]
    store_table = db.metadata.tables["Store"]
    rows = repository.session.execute(
        select(store_table.c.id, store_table.c.image.isnot(None))
        .where(store_table.c.id.in_(store_ids))
    ).all()
    flag_by_id = {row[0]: bool(row[1]) for row in rows}
    # Frozen dataclass — write through object.__setattr__ rather than rebuild.
    for dto in dtos:
        object.__setattr__(dto, "has_image", flag_by_id.get(dto.store_id, False))


# ───── List ──────────────────────────────────────────────────────────────

class GetStoresHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, options) -> Page[StoreDto]:
        page = self.repository.get(Store).paginate(
            options, StoreDto.from_entity, field_map=_FIELD_MAP
        )
        _stamp_has_image(self.repository, page.items)
        return page


@STORE_ROUTER.route("", methods=["GET"])
def get_stores():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetStoresHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info("Retrieved %d of %d stores.", len(_Page.items), _Page.total)
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)


# ───── Create ────────────────────────────────────────────────────────────

class CreateStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    # optional logo on create. Data-URL convention identical to
    # stock-item / product / recipe images; can be replaced via PATCH.
    image: str | None = Field(default=None, max_length=6_000_000)


@dataclass(slots=True)
class CreateStoreResponse:
    store_id: UUID | None = None
    duplicate: bool = False


class CreateStoreHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, req: CreateStoreRequest) -> CreateStoreResponse:
        existing = self.repository.get(Store).all()
        normalised = req.name.strip().lower()
        if any(s.name.strip().lower() == normalised for s in existing):
            return CreateStoreResponse(duplicate=True)
        store = Store(
            name=req.name.strip(),
            image=req.image.encode("utf-8") if req.image else None,
        )
        self.repository.add(store)
        self.repository.save_changes()
        return CreateStoreResponse(store_id=store.id)


@STORE_ROUTER.route("", methods=["POST"])
@has_request_body(CreateStoreRequest)
def create_store():
    _Logger = logging.getLogger(__name__)
    _Request: CreateStoreRequest = get_request_body()
    _Response = get_container().inject(CreateStoreHandler).handle(_Request)
    if _Response.duplicate:
        return business_rule_violation(
            f"A store named '{_Request.name}' already exists."
        )
    _Logger.info("Created store %s '%s'", _Response.store_id, _Request.name)
    return created(
        _Response.store_id,
        f"{STORE_ROUTER.name}.{get_stores.__name__}",
        "store_id",
        body={"store_id": _Response.store_id},
    )


# ───── Update (rename / replace image) ───────────────────────────────────

class UpdateStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    # Same data-URL convention. Send `null` to clear an existing image
    # (`clear_image=True` is the explicit clear flag — `image=None`
    # without the flag means "leave the image untouched").
    image: str | None = Field(default=None, max_length=6_000_000)
    clear_image: bool = False


@dataclass(slots=True)
class UpdateStoreResponse:
    not_found: bool = False
    duplicate: bool = False


class UpdateStoreHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self, req: UpdateStoreRequest, store_id: UUID
    ) -> UpdateStoreResponse:
        store: Store | None = self.repository.get(Store).by_id(store_id)
        if store is None:
            return UpdateStoreResponse(not_found=True)
        set_fields = req.model_fields_set
        if "name" in set_fields and req.name is not None:
            target = req.name.strip()
            normalised = target.lower()
            for s in self.repository.get(Store).all():
                if s.id != store_id and s.name.strip().lower() == normalised:
                    return UpdateStoreResponse(duplicate=True)
            store.name = target
        if req.clear_image:
            store.image = None
        elif "image" in set_fields and req.image is not None:
            store.image = req.image.encode("utf-8")
        self.repository.save_changes()
        return UpdateStoreResponse()


@STORE_ROUTER.route("/<store_id>", methods=["PATCH"])
@has_request_body(UpdateStoreRequest)
def update_store(store_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateStoreRequest = get_request_body()
    _Response = get_container().inject(UpdateStoreHandler).handle(_Request, store_id)
    if _Response.not_found:
        return not_found("Store", store_id)
    if _Response.duplicate:
        return business_rule_violation(
            f"A store named '{_Request.name}' already exists."
        )
    _Logger.info("Updated store %s", store_id)
    return no_content()


# ───── Delete ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteStoreResponse:
    not_found: bool = False
    has_products: bool = False
    product_count: int = 0
    items_affected: int = 0
    lines_affected: int = 0


class DeleteStoreHandler:
    """Referential safety:

    - `Product.store_id` is `ON DELETE RESTRICT` — products would be orphaned
      without a store, which is meaningless. The handler rejects the delete
      and surfaces the count so the user can detach products first.
    - `StockItem.usual_store_id` and `ShoppingListLine.purchased_store_id`
      are both `ON DELETE SET NULL` — they're hints; nulling them is the
      correct degrade.
    """
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, store_id: UUID) -> DeleteStoreResponse:
        store: Store | None = self.repository.get(Store).by_id(store_id)
        if store is None:
            return DeleteStoreResponse(not_found=True)
        product_count = self.repository.get(Product).count(
            EntityField(Product, "_store_id").eq(store_id)
        )
        if product_count > 0:
            return DeleteStoreResponse(
                has_products=True, product_count=product_count
            )
        items_affected = self.repository.get(StockItem).count(
            EntityField(StockItem, "usual_store_id").eq(store_id)
        )
        lines_affected = self.repository.get(ShoppingListLine).count(
            EntityField(ShoppingListLine, "purchased_store_id").eq(store_id)
        )
        self.repository.remove(store)
        self.repository.save_changes()
        return DeleteStoreResponse(
            items_affected=items_affected, lines_affected=lines_affected
        )


@STORE_ROUTER.route("/<store_id>", methods=["DELETE"])
def delete_store(store_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteStoreHandler).handle(store_id)
    if _Response.not_found:
        return not_found("Store", store_id)
    if _Response.has_products:
        return business_rule_violation(
            f"Can't delete a store with {_Response.product_count} linked "
            f"product(s). Detach or delete those first."
        )
    _Logger.info(
        "Deleted store %s; %d stock item(s) and %d shopping-line(s) had their "
        "store reference nulled",
        store_id, _Response.items_affected, _Response.lines_affected,
    )
    return ok({
        "items_affected": _Response.items_affected,
        "lines_affected": _Response.lines_affected,
    })


# ───── Image route ───────────────────────────────────────────────────────

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


@STORE_ROUTER.route("/<store_id>/image", methods=["GET"])
def get_store_image(store_id):
    repository = SqlAlchemyRepository()
    store = repository.get(Store).by_id(store_id)
    if store is None:
        return not_found(Store.__name__, store_id)
    decoded = _decode_data_url(getattr(store, "image", None))
    if decoded is None:
        return not_found(Store.__name__, store_id)
    mime, raw = decoded
    return Response(
        raw,
        mimetype=mime,
        headers={"Cache-Control": "no-cache"},
    )
