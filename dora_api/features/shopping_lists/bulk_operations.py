"""Bulk-line and reorder endpoints.

Separated from `manage_shopping_list_lines.py` so the single-line CRUD
flow stays narrow and these wider-blast-radius operations live together.

Endpoints:

  POST /api/shopping-lists/<id>/lines/bulk-tick
      Tick (or untick) a set of lines in one round-trip. Used by the
      multi-select "tick all selected" action on the detail page.

  POST /api/shopping-lists/<id>/lines/reorder
      Persist a new line order. The request body lists line_ids in the
      desired order; the handler writes the `sequence` column accordingly.
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.shopping_list import ShoppingListLine
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import (bad_request, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# ───── Bulk tick / untick ─────────────────────────────────────────────────

class BulkTickRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line_ids: List[UUID]
    # `True` ticks, `False` unticks. We force the caller to be explicit
    # rather than toggling each line — toggling a mixed selection (some
    # ticked, some not) has ambiguous semantics.
    is_ticked: bool


@dataclass(slots=True)
class BulkTickResponse:
    updated_count: int = 0


class BulkTickHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: BulkTickRequest, shopping_list_id: UUID) -> BulkTickResponse:
        if not request.line_ids:
            return BulkTickResponse(updated_count=0)

        # Constrain to lines on the named list — protects against a caller
        # passing line_ids that belong to a different list.
        lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
            & EntityField(ShoppingListLine, "id").in_([str(lid) for lid in request.line_ids])
        )
        updated = 0
        for line in lines:
            if line.is_ticked != request.is_ticked:
                line.is_ticked = request.is_ticked
                updated += 1
        if updated:
            self.repository.save_changes()
        return BulkTickResponse(updated_count=updated)


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/lines/bulk-tick", methods=["POST"])
@has_request_body(BulkTickRequest)
def bulk_tick(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: BulkTickRequest = get_request_body()
    _Response = BulkTickHandler(SqlAlchemyRepository()).handle(_Request, shopping_list_id)
    _Logger.info(
        f"Bulk-{'tick' if _Request.is_ticked else 'untick'} on list {shopping_list_id}: "
        f"updated {_Response.updated_count} of {len(_Request.line_ids)} requested"
    )
    return ok({"updated_count": _Response.updated_count})


# ───── Reorder ────────────────────────────────────────────────────────────

class ReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Line ids in the desired display order, top-to-bottom. Missing lines
    # (any line on the list not in this list) keep their existing sequence
    # and end up after the reordered ones.
    line_ids: List[UUID]


@dataclass(slots=True)
class ReorderResponse:
    list_not_found: bool = False
    mismatched: List[UUID] = None  # type: ignore[assignment]
    reordered_count: int = 0

    def __post_init__(self):
        if self.mismatched is None:
            self.mismatched = []


class ReorderHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: ReorderRequest, shopping_list_id: UUID) -> ReorderResponse:
        # Pull every line on the list so we can both validate the request
        # and assign sequences in a single pass.
        all_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
        )
        by_id = {l.id: l for l in all_lines}
        mismatched = [lid for lid in request.line_ids if lid not in by_id]
        if mismatched:
            return ReorderResponse(mismatched=mismatched)

        # Assign new sequences in the order the caller specified. Lines
        # not mentioned keep going after, preserving their relative order.
        next_seq = 0
        seen: set[UUID] = set()
        for lid in request.line_ids:
            line = by_id[lid]
            line.sequence = next_seq
            next_seq += 1
            seen.add(lid)

        leftovers = sorted(
            (l for l in all_lines if l.id not in seen),
            key=lambda l: l.sequence,
        )
        for line in leftovers:
            line.sequence = next_seq
            next_seq += 1

        self.repository.save_changes()
        return ReorderResponse(reordered_count=len(request.line_ids))


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/lines/reorder", methods=["POST"])
@has_request_body(ReorderRequest)
def reorder_lines(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: ReorderRequest = get_request_body()
    _Response = ReorderHandler(SqlAlchemyRepository()).handle(_Request, shopping_list_id)
    if _Response.mismatched:
        return bad_request(
            "Some line ids don't belong to this list.",
            detail=", ".join(str(lid) for lid in _Response.mismatched),
        )
    _Logger.info(
        f"Reordered {_Response.reordered_count} line(s) on list {shopping_list_id}"
    )
    return no_content()
