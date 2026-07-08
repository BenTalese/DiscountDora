"""Create / update / delete / archive / copy / finish for ShoppingList.

Bundled into one file because most of these handlers are 10-20 lines and
they share the "primary list is unique" invariant — keeping them together
makes that contract obvious. Finish + copy live here too because they're
shopping-list-scoped actions, not line-scoped.
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DONE, SHOPPING_LIST_STATUS_SHOPPING,
    SHOPPING_LIST_STATUS_VALUES, ShoppingList, ShoppingListLine)
from dora_api.domain.entities.product import Product
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_item_price_observation import \
    StockItemPriceObservation
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.stock_status import StockStatus, level_for_status
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.shopping_lists._line_price import (
    harvest_observation_fields, line_paid_unit_price)
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, no_content,
                                                  not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.infrastructure.ports import Repository


# ───── Create ─────────────────────────────────────────────────────────────

class CreateShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, max_length=255)
    # Optional shop day for this list.
    planned_shop_date: date | None = None


@dataclass(slots=True)
class CreateShoppingListResponse:
    shopping_list_id: UUID | None = None


class CreateShoppingListHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: CreateShoppingListRequest) -> CreateShoppingListResponse:
        now = datetime.now(timezone.utc)
        # No auto-materialised date name (UX-v2): name stays NULL unless the
        # user typed one, and the API serves a date-derived display_name that
        # tracks the planned shop date if one is set later.
        name = (request.name or "").strip() or None
        new_list = ShoppingList(
            name=name,
            created_at=now,
            planned_shop_date=request.planned_shop_date,
        )
        self.repository.add(new_list)
        self.repository.save_changes()
        return CreateShoppingListResponse(shopping_list_id=new_list.id)


@SHOPPING_LIST_ROUTER.route("", methods=["POST"])
@has_request_body(CreateShoppingListRequest)
def create_shopping_list():
    _Logger = logging.getLogger(__name__)
    _Request: CreateShoppingListRequest = get_request_body()
    _Response = CreateShoppingListHandler(SqlAlchemyRepository()).handle(_Request)
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
    # Pass a string to set, or explicit `null` to clear the custom name (the
    # list then self-labels from its dates via display_name). Field unset on
    # the wire = leave the existing value alone — same convention as
    # planned_shop_date below.
    name: str | None = Field(default=None, max_length=255)
    # Lifecycle status (draft / shopping / done). Setting it to/from `done`
    # also manages completed_at. Note: this is the plain status edit — the
    # restock-and-snapshot Finish flow lives in /finish, not here.
    status: str | None = None
    # Pass an ISO date to set, or `null` (explicit) to clear.
    # Field unset on the wire = leave the existing value alone.
    planned_shop_date: date | None = None


@dataclass(slots=True)
class UpdateShoppingListResponse:
    not_found: bool = False
    invalid_status: bool = False
    done_via_finish: bool = False


class UpdateShoppingListHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: UpdateShoppingListRequest, shopping_list_id: UUID) -> UpdateShoppingListResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return UpdateShoppingListResponse(not_found=True)

        set_fields = request.model_fields_set
        # Explicit `null` (or a blank string) clears the custom name;
        # field absent = no change.
        if "name" in set_fields:
            lst.name = (request.name or "").strip() or None
        if "status" in set_fields and request.status is not None:
            if request.status not in SHOPPING_LIST_STATUS_VALUES:
                return UpdateShoppingListResponse(invalid_status=True)
            # E3 (FU-227 chunk 5): /finish is the ONLY path to `done` — it's
            # what snapshots prices, harvests observations and bumps stock
            # levels. The SPA never PATCHes `status=done`; this guard makes
            # that contract enforceable (no half-baked done list that skipped
            # the restock review). draft⇄shopping still flow through here.
            if request.status == SHOPPING_LIST_STATUS_DONE:
                return UpdateShoppingListResponse(done_via_finish=True)
            lst.status = request.status
            lst.completed_at = None
        # Chunk 7: explicit `null` clears the date; field absent = no change.
        if "planned_shop_date" in set_fields:
            lst.planned_shop_date = request.planned_shop_date

        self.repository.save_changes()
        return UpdateShoppingListResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>", methods=["PATCH"])
@has_request_body(UpdateShoppingListRequest)
def update_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: UpdateShoppingListRequest = get_request_body()
    _Response = UpdateShoppingListHandler(SqlAlchemyRepository()).handle(_Request, shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    if _Response.invalid_status:
        return business_rule_violation(
            "`status` must be one of: draft, shopping."
        )
    if _Response.done_via_finish:
        return business_rule_violation(
            "A list becomes done by finishing it — POST /finish (which "
            "snapshots prices and restocks), not PATCH status=done."
        )
    _Logger.info(f"Updated shopping list {shopping_list_id}")
    return no_content()


# ───── Delete ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteShoppingListResponse:
    not_found: bool = False


class DeleteShoppingListHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

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
    _Response = DeleteShoppingListHandler(SqlAlchemyRepository()).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(f"Deleted shopping list {shopping_list_id}")
    return no_content()


# ───── Finish (restock review) ────────────────────────────────────────────

class FinishLevelOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    stock_level_id: UUID


class FinishShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # UX-v2 restock review: per-item level choices from the finish modal.
    # Items not listed here restock to Stocked (the default). Empty /
    # absent body = restock everything to Stocked, the one-click path.
    level_overrides: list[FinishLevelOverride] = Field(default_factory=list)


@dataclass(slots=True)
class FinishShoppingListResponse:
    not_found: bool = False
    invalid_level: bool = False
    ticked_lines: int = 0


class FinishShoppingListHandler:
    """Marks the list as done. For every ticked line, set the linked stock
    item's stock level — Stocked by default (you just bought it), or the
    level the user picked in the restock-review modal (UX-v2 M12: e.g.
    knock a part-restocked item down to Low). Untouched lines are left on
    the now-done list — the caller can copy them to a new list or use the
    "move unchecked" flow.
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, request: FinishShoppingListRequest, shopping_list_id: UUID) -> FinishShoppingListResponse:
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

        # Resolve all levels once: Stocked is the default target (by status
        # identity, not name), and the UX-v2 restock-review overrides are
        # validated against the same set.
        all_levels = self.repository.get(StockLevel).all()
        levels_by_id = {level.id: level for level in all_levels}
        stocked = level_for_status(all_levels, StockStatus.STOCKED)

        overrides: dict[UUID, UUID] = {
            o.stock_item_id: o.stock_level_id for o in request.level_overrides
        }
        if any(level_id not in levels_by_id for level_id in overrides.values()):
            return FinishShoppingListResponse(invalid_level=True)

        updated = 0
        if ticked_lines:
            stock_item_ids = [l.stock_item_id for l in ticked_lines if l.stock_item_id]
            stock_items = self.repository.get(StockItem).all(
                EntityField(StockItem, "id").in_(stock_item_ids)
            ) if stock_item_ids else []
            now = datetime.now(timezone.utc)
            for item in stock_items:
                override_id = overrides.get(item.id)
                target = levels_by_id.get(override_id) if override_id else stocked
                if target is None:
                    continue
                item.stock_level = target
                item.stock_level_last_updated = now
                updated += 1

        # harvest a price observation per priced ticked line
        # (the closed loop: confirm what you paid at the till → it feeds "Your
        # prices"). After the snapshot loop above so the picked-offer fallback
        # is populated; before the status flip so the harvest shares the single
        # save_changes transaction below.
        self._harvest_observations(ticked_lines)

        lst.status = SHOPPING_LIST_STATUS_DONE
        lst.completed_at = datetime.now(timezone.utc)

        self.repository.save_changes()
        return FinishShoppingListResponse(ticked_lines=updated)

    def _harvest_observations(self, ticked_lines: list[ShoppingListLine]) -> None:
        """Turn each priced, item-anchored ticked line into one
        ``StockItemPriceObservation`` (A1 folded shape; E4 measure-vs-count).

        Idempotent under finish-button double-taps: a partial UNIQUE on
        ``shopping_list_line_id`` (LC-1) backs the pre-check here, so a second
        ``/finish`` writes nothing new. The FK is provenance only, not a sync
        link (LC-4) — later edits to the observation don't touch the line.
        """
        harvestable = [
            l for l in ticked_lines
            if l.stock_item_id is not None and line_paid_unit_price(l) is not None
        ]
        if not harvestable:
            return

        # Idempotency: skip any line that already produced an observation.
        line_ids = [l.id for l in harvestable]
        already_harvested = {
            o.shopping_list_line_id
            for o in self.repository.get(StockItemPriceObservation).all(
                EntityField(
                    StockItemPriceObservation,
                    StockItemPriceObservation.Fields.SHOPPING_LIST_LINE_ID,
                ).in_(line_ids)
            )
        }

        # Bulk-load selected products for their pack size (E4 — a sized product
        # yields a measure observation; a sizeless line a count observation).
        product_ids = [l.selected_product_id for l in harvestable if l.selected_product_id]
        products_by_id: dict[UUID, Product] = {}
        if product_ids:
            products_by_id = {
                p.id: p for p in self.repository.get(Product).all(
                    EntityField(Product, "id").in_(product_ids)
                )
            }

        now = datetime.now(timezone.utc)
        for line in harvestable:
            if line.id in already_harvested:
                continue
            unit_price = line_paid_unit_price(line)
            if unit_price is None:    # narrowed above; keep readers honest
                continue
            product = (
                products_by_id.get(line.selected_product_id)
                if line.selected_product_id else None
            )
            total_price, total_measure, unit, pack_count = harvest_observation_fields(
                unit_price=unit_price,
                quantity=line.quantity,
                size_value=product.size_value if product else None,
                size_unit=product.size_unit if product else None,
                product_pack_count=product.pack_count if product else None,
            )
            self.repository.add(StockItemPriceObservation(
                stock_item_id=line.stock_item_id,
                total_price=total_price,
                total_measure=total_measure,
                unit=unit,
                observed_at=now,
                store_id=line.purchased_store_id,
                shopping_list_line_id=line.id,
                created_at=now,
                pack_count=pack_count,
            ))


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/finish", methods=["POST"])
@has_request_body(FinishShoppingListRequest)
def finish_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: FinishShoppingListRequest = get_request_body() or FinishShoppingListRequest()
    _Response = FinishShoppingListHandler(SqlAlchemyRepository()).handle(_Request, shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    if _Response.invalid_level:
        return business_rule_violation(
            "One or more `level_overrides` reference an unknown stock level."
        )
    _Logger.info(
        f"Finished shopping list {shopping_list_id}: "
        f"{_Response.ticked_lines} items restocked"
    )
    return ok({"items_restocked": _Response.ticked_lines})


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
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

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
            # display_name, not raw name — the source may be self-labelled
            # (name NULL), and "Copy of Sat 14 Jun" beats "Copy of None".
            name = (request.name or "").strip() or f"Copy of {source.display_name}",
            created_at = now,
        )
        self.repository.add(target)

        for sl in source_lines:
            self.repository.add(ShoppingListLine(
                shopping_list_id = target.id,
                stock_item_id = sl.stock_item_id,
                quantity = sl.quantity,
                is_ticked = False,  # fresh list starts unticked
                selected_product_id = sl.selected_product_id,
                sequence = sl.sequence,
            ))
        # FU-512 unit-of-work: one commit at the end.
        self.repository.save_changes()
        return CopyShoppingListResponse(new_shopping_list_id=target.id)


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/copy", methods=["POST"])
@has_request_body(CopyShoppingListRequest)
def copy_shopping_list(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: CopyShoppingListRequest = get_request_body()
    if _Request.include not in ("all", "unticked"):
        return business_rule_violation("`include` must be 'all' or 'unticked'.")
    _Response = CopyShoppingListHandler(SqlAlchemyRepository()).handle(_Request, shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    _Logger.info(
        f"Copied shopping list {shopping_list_id} -> {_Response.new_shopping_list_id}"
    )
    return ok({"shopping_list_id": _Response.new_shopping_list_id})


# ───── Start shopping ─────────────────────────────────────────────────────
# A dedicated endpoint (not a generic PATCH) because the transition is
# meaningful enough to log and defend invariants around (e.g. can't start a
# done list). The old /stop ("pause") endpoint was removed in UX-v2: the
# lifecycle is Start shopping → Finish & restock (→ Reopen), and the merged
# single page has no separate shop surface to exit from.

@dataclass(slots=True)
class StartShoppingResponse:
    not_found: bool = False
    archived: bool = False


class StartShoppingHandler:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def handle(self, shopping_list_id: UUID) -> StartShoppingResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(shopping_list_id)
        if lst is None:
            return StartShoppingResponse(not_found=True)
        if lst.is_done:
            return StartShoppingResponse(archived=True)
        lst.status = SHOPPING_LIST_STATUS_SHOPPING
        self.repository.save_changes()
        return StartShoppingResponse()


@SHOPPING_LIST_ROUTER.route("/<shopping_list_id>/start", methods=["POST"])
def start_shopping(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = StartShoppingHandler(SqlAlchemyRepository()).handle(shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    if _Response.archived:
        return business_rule_violation(
            "Cannot start shopping on a finished list."
        )
    _Logger.info(f"Started shopping on list {shopping_list_id}")
    return no_content()
