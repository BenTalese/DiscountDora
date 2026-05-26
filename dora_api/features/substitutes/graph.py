"""N7 — undirected stock-item substitute graph.

Endpoints:

  GET    /api/substitutes/graph         — full nodes + edges payload
  POST   /api/substitutes                — add/upsert an undirected pair
  DELETE /api/substitutes                — remove an undirected pair

Pairs are stored canonically (stock_item_a_id < stock_item_b_id) so each
unordered pair has exactly one row; callers go through `canonical_pair()`
before reading or writing. The graph endpoint includes every stock item
as a node (so the "show isolated items" toggle on the frontend has
something to surface) and only the pairs as edges.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import SUBSTITUTES_ROUTER
from dora_api.features.substitutes.canonical import canonical_pair
from dora_api.infrastructure.api_response import (business_rule_violation, ok,
                                                  no_content, not_found)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_Logger = logging.getLogger(__name__)


# ───── GET /graph ─────────────────────────────────────────────────────────

@dataclass(slots=True)
class GraphNodeDto:
    id: UUID
    name: str
    level: str | None
    group_id: UUID | None


@dataclass(slots=True)
class GraphEdgeDto:
    a: UUID
    b: UUID
    notes: str | None


class GetSubstitutesGraphHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> dict:
        items: List[StockItem] = self.repository.get(StockItem).all()
        levels = {l.id: l for l in self.repository.get(StockLevel).all()}

        nodes = [
            GraphNodeDto(
                id=item.id,
                name=item.name,
                level=(levels.get(item._stock_level_id).name  # noqa: SLF001
                       if item._stock_level_id and item._stock_level_id in levels
                       else None),
                group_id=item._stock_group_id,  # noqa: SLF001
            )
            for item in items
        ]

        _Assoc = db.metadata.tables["StockItemSubstitute"]
        rows = db.session.execute(
            select(
                _Assoc.c.stock_item_a_id,
                _Assoc.c.stock_item_b_id,
                _Assoc.c.notes,
            )
        ).all()
        edges = [
            GraphEdgeDto(a=row[0], b=row[1], notes=row[2])
            for row in rows
        ]

        return {
            "nodes": [
                {"id": n.id, "name": n.name, "level": n.level, "group_id": n.group_id}
                for n in nodes
            ],
            "edges": [
                {"a": e.a, "b": e.b, "notes": e.notes} for e in edges
            ],
        }


@SUBSTITUTES_ROUTER.route("/graph", methods=["GET"])
def get_substitutes_graph():
    _Result = get_container().inject(GetSubstitutesGraphHandler).handle()
    return ok(_Result)


# ───── POST / — add or update a pair ──────────────────────────────────────

class PairRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    a: UUID
    b: UUID
    notes: str | None = Field(default=None, max_length=2000)


@dataclass(slots=True)
class PairResponse:
    is_self: bool = False
    a_not_found: bool = False
    b_not_found: bool = False
    created: bool = False
    updated: bool = False
    removed: bool = False


class UpsertPairHandler:
    """Idempotent upsert. If the pair already exists and notes are supplied,
    the notes are overwritten; otherwise the row is left untouched. If the
    pair doesn't exist, it's inserted."""

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: PairRequest) -> PairResponse:
        if request.a == request.b:
            return PairResponse(is_self=True)
        if not self.repository.get(StockItem).exists(request.a):
            return PairResponse(a_not_found=True)
        if not self.repository.get(StockItem).exists(request.b):
            return PairResponse(b_not_found=True)

        a_id, b_id = canonical_pair(request.a, request.b)
        _Assoc = db.metadata.tables["StockItemSubstitute"]
        existing = db.session.execute(
            select(_Assoc.c.stock_item_a_id).where(
                (_Assoc.c.stock_item_a_id == a_id)
                & (_Assoc.c.stock_item_b_id == b_id)
            )
        ).first()

        if existing is None:
            db.session.execute(
                _Assoc.insert().values(
                    stock_item_a_id=a_id,
                    stock_item_b_id=b_id,
                    notes=request.notes,
                    created_at=datetime.now(timezone.utc),
                )
            )
            self.repository.save_changes()
            return PairResponse(created=True)

        # Only touch notes if the caller actually sent the field. Sending
        # an explicit null clears them.
        if "notes" in request.model_fields_set:
            db.session.execute(
                _Assoc.update()
                .where(
                    (_Assoc.c.stock_item_a_id == a_id)
                    & (_Assoc.c.stock_item_b_id == b_id)
                )
                .values(notes=request.notes)
            )
            self.repository.save_changes()
            return PairResponse(updated=True)
        return PairResponse()


@SUBSTITUTES_ROUTER.route("", methods=["POST"])
@has_request_body(PairRequest)
def upsert_substitute_pair():
    _Request: PairRequest = get_request_body()
    _Response = get_container().inject(UpsertPairHandler).handle(_Request)
    if _Response.is_self:
        return business_rule_violation("A stock item can't be its own substitute.")
    if _Response.a_not_found:
        return not_found("StockItem", _Request.a)
    if _Response.b_not_found:
        return not_found("StockItem", _Request.b)
    _Logger.info(
        "Substitute pair %s/%s: created=%s updated=%s",
        _Request.a, _Request.b, _Response.created, _Response.updated,
    )
    return ok({
        "created": _Response.created,
        "updated": _Response.updated,
    })


# ───── DELETE / — remove a pair ───────────────────────────────────────────

class DeletePairHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: PairRequest) -> PairResponse:
        if request.a == request.b:
            return PairResponse(is_self=True)
        a_id, b_id = canonical_pair(request.a, request.b)
        _Assoc = db.metadata.tables["StockItemSubstitute"]
        result = db.session.execute(
            _Assoc.delete().where(
                (_Assoc.c.stock_item_a_id == a_id)
                & (_Assoc.c.stock_item_b_id == b_id)
            )
        )
        self.repository.save_changes()
        return PairResponse(removed=result.rowcount > 0)


# DELETE uses query params (a, b) rather than a body — the request
# middleware only deserialises POST/PATCH/PUT bodies, and a, b are short
# enough to live in the URL without trouble.
@SUBSTITUTES_ROUTER.route("", methods=["DELETE"])
def delete_substitute_pair():
    from flask import request
    raw_a = request.args.get("a", "")
    raw_b = request.args.get("b", "")
    try:
        request_dto = PairRequest(a=UUID(raw_a), b=UUID(raw_b))
    except (ValueError, TypeError):
        return business_rule_violation("Both 'a' and 'b' must be UUID query params.")
    _Response = get_container().inject(DeletePairHandler).handle(request_dto)
    if _Response.is_self:
        return business_rule_violation("A stock item can't be its own substitute.")
    if not _Response.removed:
        return not_found("StockItemSubstitute pair", f"{request_dto.a}↔{request_dto.b}")
    _Logger.info("Removed substitute pair %s↔%s", request_dto.a, request_dto.b)
    return no_content()
