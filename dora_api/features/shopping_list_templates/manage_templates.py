"""CRUD + instantiate + snapshot for ShoppingListTemplate.

Templates are small and the endpoints share the same imports, so they
live together in one file. Endpoints:

  GET    /api/shopping-list-templates             — list summaries
  GET    /api/shopping-list-templates/<id>        — full detail with lines
  POST   /api/shopping-list-templates             — create (optionally with lines)
  PATCH  /api/shopping-list-templates/<id>        — rename
  DELETE /api/shopping-list-templates/<id>
  POST   /api/shopping-list-templates/<id>/lines  — add a line
  DELETE /api/shopping-list-templates/<id>/lines/<line_id>
  POST   /api/shopping-list-templates/<id>/instantiate     — create a shopping list from this template
  POST   /api/shopping-list-templates/from-list/<list_id>  — snapshot a list as a new template
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.shopping_list_template import (
    ShoppingListTemplate, ShoppingListTemplateLine,
)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import SHOPPING_LIST_TEMPLATE_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ───── DTOs ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class TemplateLineDto:
    line_id: UUID
    stock_item_id: UUID
    stock_item_name: str
    quantity: int | None
    sequence: int


@dataclass(frozen=True, slots=True)
class TemplateSummaryDto:
    template_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    line_count: int


@dataclass(frozen=True, slots=True)
class TemplateDetailDto:
    template_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    lines: List[TemplateLineDto] = field(default_factory=list)


# ───── List summaries ────────────────────────────────────────────────────

class GetTemplatesHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[TemplateSummaryDto]:
        templates: List[ShoppingListTemplate] = self.repository.get(ShoppingListTemplate).all()
        if not templates:
            return []
        all_lines: List[ShoppingListTemplateLine] = self.repository.get(ShoppingListTemplateLine).all()
        counts: dict[UUID, int] = {}
        for line in all_lines:
            counts[line.template_id] = counts.get(line.template_id, 0) + 1
        summaries = [
            TemplateSummaryDto(
                template_id = t.id,
                name = t.name,
                created_at = t.created_at,
                updated_at = t.updated_at,
                line_count = counts.get(t.id, 0),
            )
            for t in templates
        ]
        # Recently-updated first — the template you tweaked today is the
        # one you probably want to grab next.
        summaries.sort(key=lambda s: s.updated_at, reverse=True)
        return summaries


@SHOPPING_LIST_TEMPLATE_ROUTER.route("", methods=["GET"])
def get_templates():
    _Logger = logging.getLogger(__name__)
    _Result = get_container().inject(GetTemplatesHandler).handle()
    _Logger.debug("Returned %d template summaries", len(_Result))
    return ok(_Result)


# ───── Get detail ────────────────────────────────────────────────────────

class GetTemplateDetailHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, template_id: UUID) -> TemplateDetailDto | None:
        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is None:
            return None
        lines: List[ShoppingListTemplateLine] = self.repository.get(ShoppingListTemplateLine).all(
            EntityField(ShoppingListTemplateLine, "template_id").eq(template_id)
        )
        lines.sort(key=lambda l: (l.sequence, l.id))

        # Resolve stock item names in one batch so we don't N+1.
        stock_item_ids = list({l.stock_item_id for l in lines})
        items: dict[UUID, StockItem] = {}
        if stock_item_ids:
            items = {
                i.id: i for i in self.repository.get(StockItem).all(
                    EntityField(StockItem, "id").in_(stock_item_ids)
                )
            }

        line_dtos = [
            TemplateLineDto(
                line_id = l.id,
                stock_item_id = l.stock_item_id,
                stock_item_name = items[l.stock_item_id].name
                    if l.stock_item_id in items else "(missing item)",
                quantity = l.quantity,
                sequence = l.sequence,
            )
            for l in lines
        ]
        return TemplateDetailDto(
            template_id = template.id,
            name = template.name,
            created_at = template.created_at,
            updated_at = template.updated_at,
            lines = line_dtos,
        )


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>", methods=["GET"])
def get_template_detail(template_id: UUID):
    _Result = get_container().inject(GetTemplateDetailHandler).handle(template_id)
    if _Result is None:
        return not_found("ShoppingListTemplate", template_id)
    return ok(_Result)


# ───── Create template ───────────────────────────────────────────────────

class CreateTemplateLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    quantity: int | None = Field(default=1, ge=0)


class CreateTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    lines: List[CreateTemplateLineInput] = Field(default_factory=list)


@dataclass(slots=True)
class CreateTemplateResponse:
    template_id: UUID | None = None


class CreateTemplateHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateTemplateRequest) -> CreateTemplateResponse:
        now = datetime.now(timezone.utc)
        template = ShoppingListTemplate(
            name = request.name.strip(),
            created_at = now,
            updated_at = now,
        )
        self.repository.add(template)
        self.repository.save_changes()

        # Lines added in submission order — sequence reflects that order so
        # downstream rendering and instantiation preserve intent.
        for idx, line in enumerate(request.lines):
            self.repository.add(ShoppingListTemplateLine(
                template_id = template.id,
                stock_item_id = line.stock_item_id,
                quantity = line.quantity,
                sequence = idx,
            ))
        if request.lines:
            self.repository.save_changes()
        return CreateTemplateResponse(template_id=template.id)


@SHOPPING_LIST_TEMPLATE_ROUTER.route("", methods=["POST"])
@has_request_body(CreateTemplateRequest)
def create_template():
    _Logger = logging.getLogger(__name__)
    _Request: CreateTemplateRequest = get_request_body()
    _Response = get_container().inject(CreateTemplateHandler).handle(_Request)
    _Logger.info(
        f"Created template {_Response.template_id} '{_Request.name}' with {len(_Request.lines)} line(s)"
    )
    return created(
        _Response.template_id,
        f"{SHOPPING_LIST_TEMPLATE_ROUTER.name}.{get_templates.__name__}",
        "template_id",
        body={"template_id": _Response.template_id},
    )


# ───── Update template (rename) ──────────────────────────────────────────

class UpdateTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)


@dataclass(slots=True)
class UpdateTemplateResponse:
    not_found: bool = False


class UpdateTemplateHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateTemplateRequest, template_id: UUID) -> UpdateTemplateResponse:
        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is None:
            return UpdateTemplateResponse(not_found=True)
        if "name" in request.model_fields_set and request.name is not None:
            template.name = request.name.strip()
        template.updated_at = datetime.now(timezone.utc)
        self.repository.save_changes()
        return UpdateTemplateResponse()


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>", methods=["PATCH"])
@has_request_body(UpdateTemplateRequest)
def update_template(template_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateTemplateRequest = get_request_body()
    _Response = get_container().inject(UpdateTemplateHandler).handle(_Request, template_id)
    if _Response.not_found:
        return not_found("ShoppingListTemplate", template_id)
    _Logger.info(f"Updated template {template_id}")
    return no_content()


# ───── Delete template ───────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteTemplateResponse:
    not_found: bool = False


class DeleteTemplateHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, template_id: UUID) -> DeleteTemplateResponse:
        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is None:
            return DeleteTemplateResponse(not_found=True)
        self.repository.remove(template)
        self.repository.save_changes()
        return DeleteTemplateResponse()


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>", methods=["DELETE"])
def delete_template(template_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteTemplateHandler).handle(template_id)
    if _Response.not_found:
        return not_found("ShoppingListTemplate", template_id)
    _Logger.info(f"Deleted template {template_id}")
    return no_content()


# ───── Add line to template ──────────────────────────────────────────────

class AddTemplateLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    quantity: int | None = Field(default=1, ge=0)


@dataclass(slots=True)
class AddTemplateLineResponse:
    line_id: UUID | None = None
    template_not_found: bool = False
    item_not_found: bool = False
    already_on_template: bool = False


class AddTemplateLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: AddTemplateLineRequest, template_id: UUID) -> AddTemplateLineResponse:
        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is None:
            return AddTemplateLineResponse(template_not_found=True)
        item: StockItem | None = self.repository.get(StockItem).by_id(request.stock_item_id)
        if item is None:
            return AddTemplateLineResponse(item_not_found=True)

        # Same unique-per-item rule as ShoppingList: adding twice folds.
        existing = self.repository.get(ShoppingListTemplateLine).one(
            EntityField(ShoppingListTemplateLine, "template_id").eq(template_id)
            & EntityField(ShoppingListTemplateLine, "stock_item_id").eq(request.stock_item_id)
        )
        if existing is not None:
            return AddTemplateLineResponse(line_id=existing.id, already_on_template=True)

        siblings = self.repository.get(ShoppingListTemplateLine).all(
            EntityField(ShoppingListTemplateLine, "template_id").eq(template_id)
        )
        next_sequence = (max((l.sequence for l in siblings), default=-1)) + 1
        line = ShoppingListTemplateLine(
            template_id = template_id,
            stock_item_id = request.stock_item_id,
            quantity = request.quantity,
            sequence = next_sequence,
        )
        self.repository.add(line)
        template.updated_at = datetime.now(timezone.utc)
        self.repository.save_changes()
        return AddTemplateLineResponse(line_id=line.id)


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>/lines", methods=["POST"])
@has_request_body(AddTemplateLineRequest)
def add_template_line(template_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: AddTemplateLineRequest = get_request_body()
    _Response = get_container().inject(AddTemplateLineHandler).handle(_Request, template_id)
    if _Response.template_not_found:
        return not_found("ShoppingListTemplate", template_id)
    if _Response.item_not_found:
        return not_found("StockItem", _Request.stock_item_id)
    _Logger.info(
        f"Added template line {_Response.line_id} to {template_id} "
        f"(already_on_template={_Response.already_on_template})"
    )
    return ok({"line_id": _Response.line_id, "already_on_template": _Response.already_on_template})


# ───── Delete line ───────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteTemplateLineResponse:
    not_found: bool = False


class DeleteTemplateLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, template_id: UUID, line_id: UUID) -> DeleteTemplateLineResponse:
        line: ShoppingListTemplateLine | None = self.repository.get(ShoppingListTemplateLine).by_id(line_id)
        if line is None or line.template_id != template_id:
            return DeleteTemplateLineResponse(not_found=True)
        self.repository.remove(line)

        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is not None:
            template.updated_at = datetime.now(timezone.utc)
        self.repository.save_changes()
        return DeleteTemplateLineResponse()


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>/lines/<line_id>", methods=["DELETE"])
def delete_template_line(template_id: UUID, line_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteTemplateLineHandler).handle(template_id, line_id)
    if _Response.not_found:
        return not_found("ShoppingListTemplateLine", line_id)
    _Logger.info(f"Deleted template line {line_id} from template {template_id}")
    return no_content()


# ───── Update template line (quantity) ───────────────────────────────────

class UpdateTemplateLineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: int | None = Field(default=None, ge=0)


@dataclass(slots=True)
class UpdateTemplateLineResponse:
    not_found: bool = False


class UpdateTemplateLineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self,
        request: UpdateTemplateLineRequest,
        template_id: UUID,
        line_id: UUID,
    ) -> UpdateTemplateLineResponse:
        line: ShoppingListTemplateLine | None = self.repository.get(ShoppingListTemplateLine).by_id(line_id)
        if line is None or line.template_id != template_id:
            return UpdateTemplateLineResponse(not_found=True)
        if "quantity" in request.model_fields_set:
            line.quantity = request.quantity

        # Bump the template's updated_at so summaries sort sensibly.
        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is not None:
            template.updated_at = datetime.now(timezone.utc)
        self.repository.save_changes()
        return UpdateTemplateLineResponse()


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>/lines/<line_id>", methods=["PATCH"])
@has_request_body(UpdateTemplateLineRequest)
def update_template_line(template_id: UUID, line_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateTemplateLineRequest = get_request_body()
    _Response = get_container().inject(UpdateTemplateLineHandler).handle(
        _Request, template_id, line_id,
    )
    if _Response.not_found:
        return not_found("ShoppingListTemplateLine", line_id)
    _Logger.debug(f"Updated template line {line_id} on template {template_id}")
    return no_content()


# ───── Instantiate template → new shopping list ──────────────────────────

class InstantiateTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Optional name override; if absent, defaults to "<template_name> · <today>".
    name: str | None = None
    # Optional: make the new list primary (clearing the existing primary).
    make_primary: bool = False


@dataclass(slots=True)
class InstantiateTemplateResponse:
    new_shopping_list_id: UUID | None = None
    not_found: bool = False
    line_count: int = 0


class InstantiateTemplateHandler:
    """Creates a new ShoppingList from the template's lines.

    Stock items that have since been deleted are silently skipped (we'd
    otherwise blow up creating a line pointing at a missing FK). Selected
    products are intentionally not carried — see the template entity
    docstring for the reasoning.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: InstantiateTemplateRequest, template_id: UUID) -> InstantiateTemplateResponse:
        template: ShoppingListTemplate | None = self.repository.get(ShoppingListTemplate).by_id(template_id)
        if template is None:
            return InstantiateTemplateResponse(not_found=True)

        now = datetime.now(timezone.utc)
        name = (request.name or "").strip() or f"{template.name} · {now.strftime('%a %d %b')}"

        if request.make_primary:
            existing_primaries = self.repository.get(ShoppingList).all(
                EntityField(ShoppingList, ShoppingList.Fields.IS_PRIMARY).eq(True)
            )
            for p in existing_primaries:
                p.is_primary = False

        new_list = ShoppingList(name=name, created_at=now, is_primary=request.make_primary)
        self.repository.add(new_list)
        self.repository.save_changes()

        template_lines: List[ShoppingListTemplateLine] = self.repository.get(ShoppingListTemplateLine).all(
            EntityField(ShoppingListTemplateLine, "template_id").eq(template_id)
        )
        template_lines.sort(key=lambda l: l.sequence)

        # Bulk-check which stock items still exist so we skip orphans.
        existing_ids: set[UUID] = set()
        if template_lines:
            existing = self.repository.get(StockItem).all(
                EntityField(StockItem, "id").in_([l.stock_item_id for l in template_lines])
            )
            existing_ids = {i.id for i in existing}

        added = 0
        for idx, tl in enumerate(template_lines):
            if tl.stock_item_id not in existing_ids:
                continue
            self.repository.add(ShoppingListLine(
                shopping_list_id = new_list.id,
                stock_item_id = tl.stock_item_id,
                quantity = tl.quantity,
                sequence = idx,
            ))
            added += 1
        if added:
            self.repository.save_changes()
        return InstantiateTemplateResponse(
            new_shopping_list_id=new_list.id, line_count=added,
        )


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/<template_id>/instantiate", methods=["POST"])
@has_request_body(InstantiateTemplateRequest)
def instantiate_template(template_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: InstantiateTemplateRequest = get_request_body()
    _Response = get_container().inject(InstantiateTemplateHandler).handle(_Request, template_id)
    if _Response.not_found:
        return not_found("ShoppingListTemplate", template_id)
    _Logger.info(
        f"Instantiated template {template_id} -> list {_Response.new_shopping_list_id} "
        f"({_Response.line_count} lines)"
    )
    return ok({
        "shopping_list_id": _Response.new_shopping_list_id,
        "line_count": _Response.line_count,
    })


# ───── Snapshot existing list → new template ─────────────────────────────

class SnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    # If True, every line on the source list ends up on the template.
    # If False (default), only unticked lines are saved — the assumption
    # is "this is what I usually need; the ticked items were one-offs".
    include_ticked: bool = False


@dataclass(slots=True)
class SnapshotResponse:
    template_id: UUID | None = None
    source_not_found: bool = False
    line_count: int = 0


class SnapshotFromListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: SnapshotRequest, source_list_id: UUID) -> SnapshotResponse:
        source: ShoppingList | None = self.repository.get(ShoppingList).by_id(source_list_id)
        if source is None:
            return SnapshotResponse(source_not_found=True)

        now = datetime.now(timezone.utc)
        template = ShoppingListTemplate(
            name = (request.name or "").strip() or f"Template from {source.name}",
            created_at = now,
            updated_at = now,
        )
        self.repository.add(template)
        self.repository.save_changes()

        source_lines: List[ShoppingListLine] = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(source_list_id)
        )
        if not request.include_ticked:
            source_lines = [l for l in source_lines if not l.is_ticked]
        source_lines.sort(key=lambda l: l.sequence)

        added = 0
        for idx, sl in enumerate(source_lines):
            self.repository.add(ShoppingListTemplateLine(
                template_id = template.id,
                stock_item_id = sl.stock_item_id,
                quantity = sl.quantity if sl.quantity is not None else 1,
                sequence = idx,
            ))
            added += 1
        if added:
            self.repository.save_changes()
        return SnapshotResponse(template_id=template.id, line_count=added)


@SHOPPING_LIST_TEMPLATE_ROUTER.route("/from-list/<source_list_id>", methods=["POST"])
@has_request_body(SnapshotRequest)
def snapshot_from_list(source_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: SnapshotRequest = get_request_body()
    _Response = get_container().inject(SnapshotFromListHandler).handle(_Request, source_list_id)
    if _Response.source_not_found:
        return not_found("ShoppingList", source_list_id)
    _Logger.info(
        f"Snapshotted list {source_list_id} -> template {_Response.template_id} "
        f"({_Response.line_count} lines)"
    )
    return ok({
        "template_id": _Response.template_id,
        "line_count": _Response.line_count,
    })
