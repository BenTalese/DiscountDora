"""Tool CRUD (C-4 Chunk 5) — the user-configurable kitchen-tool vocabulary.
Mirrors manage_cuisines.py; usage counts come from the RecipeTool assoc.

Endpoints:
  GET    /api/tools        — list all (with recipe counts), ordered
  POST   /api/tools        — create
  PATCH  /api/tools/<id>   — rename
  DELETE /api/tools/<id>   — delete (RecipeTool links cascade away)
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from dora_api.app import db
from dora_api.domain.entities.tool import Tool
from dora_api.features.routers import TOOL_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class ToolDto:
    tool_id: UUID
    name: str
    sequence: int
    recipe_count: int


def _recipe_counts() -> dict[UUID, int]:
    table = db.metadata.tables["RecipeTool"]
    rows = db.session.execute(
        select(table.c.tool_id, func.count(table.c.recipe_id))
        .group_by(table.c.tool_id)
    ).all()
    return {row[0]: int(row[1] or 0) for row in rows}


# ───── List ──────────────────────────────────────────────────────────────

class GetToolsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[ToolDto]:
        tools: List[Tool] = self.repository.get(Tool).all()
        counts = _recipe_counts()
        out = [
            ToolDto(
                tool_id=t.id,
                name=t.name,
                sequence=t.sequence,
                recipe_count=counts.get(t.id, 0),
            )
            for t in tools
        ]
        out.sort(key=lambda t: (t.sequence, t.name.lower()))
        return out


@TOOL_ROUTER.route("", methods=["GET"])
def get_tools():
    return ok(get_container().inject(GetToolsHandler).handle())


# ───── Create ────────────────────────────────────────────────────────────

class CreateToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class CreateToolResponse:
    tool_id: UUID | None = None
    duplicate: bool = False


class CreateToolHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateToolRequest) -> CreateToolResponse:
        existing = self.repository.get(Tool).all()
        normalised = request.name.strip().lower()
        if any(t.name.strip().lower() == normalised for t in existing):
            return CreateToolResponse(duplicate=True)
        next_seq = max((t.sequence for t in existing), default=-1) + 1
        tool = Tool(name=request.name.strip(), sequence=next_seq)
        self.repository.add(tool)
        self.repository.save_changes()
        return CreateToolResponse(tool_id=tool.id)


@TOOL_ROUTER.route("", methods=["POST"])
@has_request_body(CreateToolRequest)
def create_tool():
    _Logger = logging.getLogger(__name__)
    _Request: CreateToolRequest = get_request_body()
    _Response = get_container().inject(CreateToolHandler).handle(_Request)
    if _Response.duplicate:
        return business_rule_violation(f"A tool named '{_Request.name}' already exists.")
    _Logger.info(f"Created tool {_Response.tool_id} '{_Request.name}'")
    return created(
        _Response.tool_id,
        f"{TOOL_ROUTER.name}.{get_tools.__name__}",
        "tool_id",
        body={"tool_id": _Response.tool_id},
    )


# ───── Rename ────────────────────────────────────────────────────────────

class UpdateToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class UpdateToolResponse:
    not_found: bool = False
    duplicate: bool = False


class UpdateToolHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateToolRequest, tool_id: UUID) -> UpdateToolResponse:
        tool: Tool | None = self.repository.get(Tool).by_id(tool_id)
        if tool is None:
            return UpdateToolResponse(not_found=True)
        target = request.name.strip()
        normalised = target.lower()
        for t in self.repository.get(Tool).all():
            if t.id != tool_id and t.name.strip().lower() == normalised:
                return UpdateToolResponse(duplicate=True)
        tool.name = target
        self.repository.save_changes()
        return UpdateToolResponse()


@TOOL_ROUTER.route("/<tool_id>", methods=["PATCH"])
@has_request_body(UpdateToolRequest)
def update_tool(tool_id: UUID):
    _Request: UpdateToolRequest = get_request_body()
    _Response = get_container().inject(UpdateToolHandler).handle(_Request, tool_id)
    if _Response.not_found:
        return not_found("Tool", tool_id)
    if _Response.duplicate:
        return business_rule_violation(f"A tool named '{_Request.name}' already exists.")
    return ok({"tool_id": tool_id})


# ───── Delete ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteToolResponse:
    not_found: bool = False
    recipes_affected: int = 0


class DeleteToolHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, tool_id: UUID) -> DeleteToolResponse:
        tool: Tool | None = self.repository.get(Tool).by_id(tool_id)
        if tool is None:
            return DeleteToolResponse(not_found=True)
        affected = _recipe_counts().get(tool_id, 0)
        self.repository.remove(tool)
        self.repository.save_changes()
        return DeleteToolResponse(recipes_affected=affected)


@TOOL_ROUTER.route("/<tool_id>", methods=["DELETE"])
def delete_tool(tool_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteToolHandler).handle(tool_id)
    if _Response.not_found:
        return not_found("Tool", tool_id)
    _Logger.info(f"Deleted tool {tool_id}; {_Response.recipes_affected} link(s) removed")
    return ok({"recipes_affected": _Response.recipes_affected})
