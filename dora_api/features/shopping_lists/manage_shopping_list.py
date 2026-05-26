"""Create / update / delete / archive / copy / finish for ShoppingList.

Bundled into one file because most of these handlers are 10-20 lines and
they share the "primary list is unique" invariant — keeping them together
makes that contract obvious. Finish + copy live here too because they're
shopping-list-scoped actions, not line-scoped.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.shopping_list import (ShoppingList,
                                                    ShoppingListLine)
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# ───── Create ─────────────────────────────────────────────────────────────

class CreateShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=255)
    # If true the new list is set as primary (unsetting whatever currently is).
    make_primary: bool = False


@dataclass(slots=True)
class CreateShoppingListResponse:
    shopping_list_id: UUID | None = None


class CreateShoppingListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateShoppingListRequest) -> CreateShoppingListResponse:
        now = datetime.now(timezone.utc)
        # Default name = today's date — most users want a list-per-shop.
        # Auto-naming keeps the create UX one click.
        name = (request.name or "").strip() or now.strftime("%a %d %b")

        # Setting primary atomically: clear any existing primary first.
        if request.make_primary:
            existing_primary = self.repository.get(ShoppingList).all(
                EntityField(ShoppingList, ShoppingList.Fields.IS_PRIMARY).eq(True)
            )
            for p in existing_primary:
                p.is_primary = False

        new_list = ShoppingList(
            name = name,
            created_at = now,
            is_primary = request.make_primary,
        )
        self.repository.add(new_list)
        self.repository.save_changes()
        return CreateShoppingListResponse(shopping_list_id=new_list.id)


@SHOPPING_LIST_ROUTER.route("", methods=["POST"])
@has_request_body(CreateShoppingListRequest)
def create_shopping_list():
    _Logger = logging.getLogger(__name__)
    _Request: CreateShoppingListRequest = get_request_body()
    _Response = get_container().inject(CreateShoppingListHandler).handle(_Request)
    _Logger.info(f"Created shopping list {_Response.shopping_list_id}")
    from dora_api.features.shopping_lists.get_shopping_lists import \
        get_shopping_lists
    return created(
        _Response.shopping_list_id,
        f"{SHOPPING_LIST_ROUTER.name}.{get_shopping_lists.__name__}",
        "shopping_list_id",
        body={"shopping_list_id": _Response.shopping_list_id},
    )


# ───── Update ─────────────────────────────────────────────────────────────

class UpdateShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_primary: bool | None = None
    is_archived: bool | None = None


@dataclass(slots=True)
class UpdateShoppingListResponse:
    not_found: bool = False


class UpdateShoppingListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateShoppingListRequest, shopping_list_id: UUID) -> UpdateShoppingListResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return UpdateShoppingListResponse(not_found=True)

        set_fields = request.model_fields_set
        if "name" in set_fields and request.name is not None:
            lst.name = request.name
        if "is_archived" in set_fields and request.is_archived is not None:
            lst.is_archived = request.is_archived
            if request.is_archived and lst.completed_at is None:
                lst.completed_at = datetime.now(timezone.utc)
            elif not request.is_archived:
                lst.completed_at = None

        # When setting primary, clear the current primary first so the
        # invariant ("at most one primary list") holds. When clearing the
        # primary on the current list, just unset.
        if "is_primary" in set_fields and request.is_primary is not None:
            if request.is_primary:
                existing_primary = self.repository.get(ShoppingList).all(
                    EntityField(ShoppingList, ShoppingList.Fields.IS_PRIMARY).eq(True)
                )
                for p in existing_primary:
                    if p.id != shopping_list_id:
                        p.is_primary = False
                lst.is_primary = True
            else:
                lst.is_primary = False

        self.repository.save_changes()
        return UpdateShoppingListResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>", methods=["PATCH"])
@has_request_body(UpdateShoppingListRequest)
def update_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateShoppingListRequest = get_request_body()
    _Response = get_container().inject(UpdateShoppingListHandler).handle(_Request, shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(f"Updated shopping list {shopping_list_id}")
    return no_content()


# ───── Delete ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteShoppingListResponse:
    not_found: bool = False


class DeleteShoppingListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> DeleteShoppingListResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return DeleteShoppingListResponse(not_found=True)
        self.repository.remove(lst)
        self.repository.save_changes()
        return DeleteShoppingListResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>", methods=["DELETE"])
def delete_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteShoppingListHandler).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(f"Deleted shopping list {shopping_list_id}")
    return no_content()


# ───── Finish (review mode) ───────────────────────────────────────────────

@dataclass(slots=True)
class FinishShoppingListResponse:
    not_found: bool = False
    ticked_lines: int = 0
    new_primary_list_id: UUID | None = None


class FinishShoppingListHandler:
    """Marks the list as archived. For every ticked line, set the linked
    stock item's stock level to "Well-Stocked" (the assumption is: you
    just bought it, your pantry is restocked). Untouched lines are left
    on the now-archived list — the caller can copy them to a new list or
    use the "move unchecked to new list" flow.
    """

    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> FinishShoppingListResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return FinishShoppingListResponse(not_found=True)

        ticked_lines = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
            & EntityField(ShoppingListLine, ShoppingListLine.Fields.IS_TICKED).eq(True)
        )

        # N6: ensure every ticked line has a price snapshot. Normally
        # captured at tick time, but a line ticked before this feature
        # existed (or in a flow that bypasses the standard update path)
        # would arrive here without one. Snapshot now so reports include
        # the list.
        from dora_api.features.shopping_lists.manage_shopping_list_lines import \
            snapshot_offer_price
        for line in ticked_lines:
            if line.picked_offer_price is None:
                snapshot_offer_price(self.repository, line)

        # Look up the "Well-Stocked" level once.
        well_stocked: StockLevel | None = self.repository.get(StockLevel).one(
            EntityField(StockLevel, StockLevel.Fields.NAME).eq("Well-Stocked")
        )

        updated = 0
        if well_stocked and ticked_lines:
            stock_item_ids = [l.stock_item_id for l in ticked_lines]
            stock_items = self.repository.get(StockItem).all(
                EntityField(StockItem, "id").in_(stock_item_ids)
            )
            now = datetime.now(timezone.utc)
            for item in stock_items:
                item.stock_level = well_stocked
                item.stock_level_last_updated = now
                updated += 1

        lst.is_archived = True
        lst.is_in_progress = False
        lst.completed_at = datetime.now(timezone.utc)

        # If we just archived the primary list, promote the most recent
        # active list. Matches the spec: "Completing the primary default
        # shopping list moves the primary selection to the next available
        # shopping list by creation date".
        new_primary_id: UUID | None = None
        if lst.is_primary:
            lst.is_primary = False
            candidates = self.repository.get(ShoppingList).all(
                EntityField(ShoppingList, ShoppingList.Fields.IS_ARCHIVED).eq(False)
            )
            candidates = [c for c in candidates if c.id != shopping_list_id]
            candidates.sort(key=lambda c: c.created_at, reverse=True)
            if candidates:
                candidates[0].is_primary = True
                new_primary_id = candidates[0].id

        self.repository.save_changes()
        return FinishShoppingListResponse(
            ticked_lines=updated, new_primary_list_id=new_primary_id
        )


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/finish", methods=["POST"])
def finish_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(FinishShoppingListHandler).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        f"Finished shopping list {shopping_list_id}: "
        f"{_Response.ticked_lines} items restocked, "
        f"new primary = {_Response.new_primary_list_id}"
    )
    return ok({
        "items_restocked": _Response.ticked_lines,
        "new_primary_list_id": _Response.new_primary_list_id,
    })


# ───── Copy ────────────────────────────────────────────────────────────────

class CopyShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # If "all", copy every line. If "unticked", only the lines that weren't
    # ticked off (useful for "move unchecked to new list" flow).
    include: str = "all"
    name: str | None = Field(default=None, max_length=255)


@dataclass(slots=True)
class CopyShoppingListResponse:
    not_found: bool = False
    new_shopping_list_id: UUID | None = None


class CopyShoppingListHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CopyShoppingListRequest, shopping_list_id: UUID) -> CopyShoppingListResponse:
        source: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if source is None:
            return CopyShoppingListResponse(not_found=True)

        source_lines = self.repository.get(ShoppingListLine).all(
            EntityField(ShoppingListLine, "shopping_list_id").eq(shopping_list_id)
        )
        if request.include == "unticked":
            source_lines = [l for l in source_lines if not l.is_ticked]

        now = datetime.now(timezone.utc)
        target = ShoppingList(
            name = (request.name or "").strip() or f"Copy of {source.name}",
            created_at = now,
        )
        self.repository.add(target)
        self.repository.save_changes()

        for sl in source_lines:
            self.repository.add(ShoppingListLine(
                shopping_list_id = target.id,
                stock_item_id = sl.stock_item_id,
                quantity = sl.quantity,
                is_ticked = False,  # fresh list starts unticked
                selected_product_id = sl.selected_product_id,
                sequence = sl.sequence,
            ))
        self.repository.save_changes()
        return CopyShoppingListResponse(new_shopping_list_id=target.id)


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/copy", methods=["POST"])
@has_request_body(CopyShoppingListRequest)
def copy_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: CopyShoppingListRequest = get_request_body()
    if _Request.include not in ("all", "unticked"):
        return business_rule_violation("`include` must be 'all' or 'unticked'.")
    _Response = get_container().inject(CopyShoppingListHandler).handle(_Request, shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        f"Copied shopping list {shopping_list_id} -> {_Response.new_shopping_list_id}"
    )
    return ok({"shopping_list_id": _Response.new_shopping_list_id})


# ───── Start / Stop shopping ──────────────────────────────────────────────
# These are a single state-transition with two endpoints rather than a
# generic PATCH because the transition is meaningful enough to log and
# defend invariants around (e.g. can't start an archived list).

@dataclass(slots=True)
class StartStopResponse:
    not_found: bool = False
    archived: bool = False


class StartShoppingHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> StartStopResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return StartStopResponse(not_found=True)
        if lst.is_archived:
            return StartStopResponse(archived=True)
        lst.is_in_progress = True
        self.repository.save_changes()
        return StartStopResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/start", methods=["POST"])
def start_shopping(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(StartShoppingHandler).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    if _Response.archived:
        return business_rule_violation(
            "Cannot start shopping on an archived list."
        )
    _Logger.info(f"Started shopping on list {shopping_list_id}")
    return no_content()


class StopShoppingHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, shopping_list_id: UUID) -> StartStopResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return StartStopResponse(not_found=True)
        # Allow stop even on archived lists — it's a no-op then but the
        # endpoint is idempotent and shouldn't error.
        lst.is_in_progress = False
        self.repository.save_changes()
        return StartStopResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/stop", methods=["POST"])
def stop_shopping(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(StopShoppingHandler).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(f"Stopped shopping on list {shopping_list_id}")
    return no_content()
