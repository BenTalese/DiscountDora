"""StockGroup CRUD bundled in one file.

Groups are intentionally lightweight — just a name on a row. They're
referenced from `StockItem.stock_group_id` and surface as filter chips
on the stock overview. The pre-defined groups land via the seed; the
endpoints here let users add, rename, and delete their own.

Endpoints:

  GET    /api/stock-groups          — list all groups (with item counts)
  POST   /api/stock-groups          — create
  PATCH  /api/stock-groups/<id>     — rename
  DELETE /api/stock-groups/<id>     — delete (linked stock items go to
                                       group_id = NULL via the FK's
                                       ON DELETE SET NULL)
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import STOCK_GROUP_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class StockGroupDto:
    stock_group_id: UUID
    name: str
    item_count: int


# ───── List ──────────────────────────────────────────────────────────────

class GetStockGroupsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[StockGroupDto]:
        groups: List[StockGroup] = self.repository.get(StockGroup).all()
        # Pull every stock item once and bucket — cheaper than N round trips
        # when there are a few dozen groups.
        items = self.repository.get(StockItem).all()
        counts: dict[UUID, int] = {}
        for item in items:
            if item.stock_group is not None:
                counts[item.stock_group.id] = counts.get(item.stock_group.id, 0) + 1
        out = [
            StockGroupDto(
                stock_group_id = g.id,
                name = g.name,
                item_count = counts.get(g.id, 0),
            )
            for g in groups
        ]
        out.sort(key=lambda g: g.name.lower())
        return out


@STOCK_GROUP_ROUTER.route("", methods=["GET"])
def get_stock_groups():
    _Logger = logging.getLogger(__name__)
    _Result = get_container().inject(GetStockGroupsHandler).handle()
    _Logger.debug("Returned %d stock groups", len(_Result))
    return ok(_Result)


# ───── Create ────────────────────────────────────────────────────────────

class CreateStockGroupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class CreateStockGroupResponse:
    stock_group_id: UUID | None = None
    duplicate: bool = False


class CreateStockGroupHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateStockGroupRequest) -> CreateStockGroupResponse:
        # Case-insensitive uniqueness — "Dairy" and "dairy" shouldn't both
        # exist. The repo's `contains` would match substrings; do a strict
        # equality check by normalising in Python.
        existing = self.repository.get(StockGroup).all()
        normalised = request.name.strip().lower()
        if any(g.name.strip().lower() == normalised for g in existing):
            return CreateStockGroupResponse(duplicate=True)

        group = StockGroup(name=request.name.strip())
        self.repository.add(group)
        self.repository.save_changes()
        return CreateStockGroupResponse(stock_group_id=group.id)


@STOCK_GROUP_ROUTER.route("", methods=["POST"])
@has_request_body(CreateStockGroupRequest)
def create_stock_group():
    _Logger = logging.getLogger(__name__)
    _Request: CreateStockGroupRequest = get_request_body()
    _Response = get_container().inject(CreateStockGroupHandler).handle(_Request)
    if _Response.duplicate:
        return business_rule_violation(
            f"A stock group named '{_Request.name}' already exists."
        )
    _Logger.info(f"Created stock group {_Response.stock_group_id} '{_Request.name}'")
    return created(
        _Response.stock_group_id,
        f"{STOCK_GROUP_ROUTER.name}.{get_stock_groups.__name__}",
        "stock_group_id",
        body={"stock_group_id": _Response.stock_group_id},
    )


# ───── Rename ────────────────────────────────────────────────────────────

class UpdateStockGroupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class UpdateStockGroupResponse:
    not_found: bool = False
    duplicate: bool = False


class UpdateStockGroupHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self, request: UpdateStockGroupRequest, stock_group_id: UUID
    ) -> UpdateStockGroupResponse:
        group: StockGroup | None = self.repository.get(StockGroup).by_id(stock_group_id)
        if group is None:
            return UpdateStockGroupResponse(not_found=True)
        target = request.name.strip()
        normalised = target.lower()
        existing = self.repository.get(StockGroup).all()
        for g in existing:
            if g.id != stock_group_id and g.name.strip().lower() == normalised:
                return UpdateStockGroupResponse(duplicate=True)
        group.name = target
        self.repository.save_changes()
        return UpdateStockGroupResponse()


@STOCK_GROUP_ROUTER.route("/<stock_group_id>", methods=["PATCH"])
@has_request_body(UpdateStockGroupRequest)
def update_stock_group(stock_group_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateStockGroupRequest = get_request_body()
    _Response = get_container().inject(UpdateStockGroupHandler).handle(_Request, stock_group_id)
    if _Response.not_found:
        return not_found("StockGroup", stock_group_id)
    if _Response.duplicate:
        return business_rule_violation(
            f"A stock group named '{_Request.name}' already exists."
        )
    _Logger.info(f"Renamed stock group {stock_group_id}")
    return no_content()


# ───── Delete ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteStockGroupResponse:
    not_found: bool = False
    items_affected: int = 0


class DeleteStockGroupHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, stock_group_id: UUID) -> DeleteStockGroupResponse:
        group: StockGroup | None = self.repository.get(StockGroup).by_id(stock_group_id)
        if group is None:
            return DeleteStockGroupResponse(not_found=True)

        # Pre-count how many items will get their group nulled. The FK's
        # ON DELETE SET NULL handles the column update at the DB level —
        # we just surface the count so the UI can warn meaningfully.
        affected = self.repository.get(StockItem).count(
            EntityField(StockItem, "_stock_group_id").eq(stock_group_id)
        )
        self.repository.remove(group)
        self.repository.save_changes()
        return DeleteStockGroupResponse(items_affected=affected)


@STOCK_GROUP_ROUTER.route("/<stock_group_id>", methods=["DELETE"])
def delete_stock_group(stock_group_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteStockGroupHandler).handle(stock_group_id)
    if _Response.not_found:
        return not_found("StockGroup", stock_group_id)
    _Logger.info(
        f"Deleted stock group {stock_group_id}; "
        f"{_Response.items_affected} stock item(s) had their group nulled"
    )
    return ok({"items_affected": _Response.items_affected})
