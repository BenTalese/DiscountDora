import logging
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from flask import request

from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.stock_status import (is_low_stock, is_out_of_stock,
                                          needs_restock)
from dora_api.features.routers import STOCK_ITEM_ROUTER
from dora_api.infrastructure.api_response import bad_request, paginated
from dora_api.infrastructure.query_options import (InvalidQueryParameter,
                                                   parse_query_options)
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.field import EntityField
from dora_api.persistence.page import Page
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class StockItemDto:
    name: str
    stock_item_id: UUID
    stock_level_id: UUID
    stock_level_name: str | None
    # Status keyed to the level's ordinal sequence, plus the server-owned
    # derived predicates — so the client never matches on a level name.
    stock_level_sequence: int | None
    is_out_of_stock: bool
    is_low_stock: bool
    needs_restock: bool
    stock_location_id: UUID | None
    stock_group_id: UUID | None
    stock_level_last_updated: datetime
    expiry_date: date | None
    is_flagged: bool
    auto_add_when_low: bool
    is_open: bool
    opened_on: date | None
    last_checked_at: datetime | None
    # whether the row has an image to render. The
    # bytes themselves never travel in the list/detail JSON (the `image`
    # column is deferred); the SPA fetches them via
    # `GET /stock-items/<id>/image`, which itself falls back to a linked
    # Product's image when the stock item has none. Hydrated below.
    has_image: bool = False
    # count of linked products. Drives the "2+ products →
    # combined choice modal" decision in `AddToListButton`. 0 = generic
    # stock-item line (no offer); 1 = preselect; 2+ = open QuickAddSheet
    # so the user picks the offer + (if relevant) the target list in one
    # combined surface instead of stacking two prompts.
    linked_product_count: int = 0

    @classmethod
    def from_entity(cls, stock_item: StockItem) -> 'StockItemDto':
        level = stock_item.stock_level
        return StockItemDto(
            name = stock_item.name,
            stock_item_id = stock_item.id,
            stock_level_id = stock_item.stock_level.id,
            stock_level_name = level.name if level else None,
            stock_level_sequence = level.sequence if level else None,
            is_out_of_stock = is_out_of_stock(level),
            is_low_stock = is_low_stock(level),
            needs_restock = needs_restock(level),
            stock_location_id = stock_item.stock_location.id if stock_item.stock_location else None,
            stock_group_id = stock_item.stock_group.id if stock_item.stock_group else None,
            stock_level_last_updated = stock_item.stock_level_last_updated,
            expiry_date = stock_item.expiry_date,
            is_flagged = bool(stock_item.is_flagged),
            auto_add_when_low = bool(stock_item.auto_add_when_low),
            is_open = bool(stock_item.is_open),
            opened_on = stock_item.opened_on,
            last_checked_at = stock_item.last_checked_at,
        )


_FIELD_MAP: dict[str, EntityField] = {
    "stock_item_id": EntityField(StockItem, "id"),
    "stock_level_id": EntityField(StockItem, "_stock_level_id"),
    "stock_location_id": EntityField(StockItem, "_stock_location_id"),
    "stock_group_id": EntityField(StockItem, "_stock_group_id"),
    "is_flagged": EntityField(StockItem, StockItem.Fields.IS_FLAGGED),
    "is_open": EntityField(StockItem, StockItem.Fields.IS_OPEN),
}


class GetStockItemsHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def _base_query(self):
        return (
            self.repository
            .get(StockItem)
            .include(StockItem.Fields.STOCK_LEVEL)
            .include(StockItem.Fields.STOCK_LOCATION)
            .include(StockItem.Fields.STOCK_GROUP)
        )

    def _hydrate_linked_product_count(
        self, dtos: list[StockItemDto]
    ) -> list[StockItemDto]:
        """C-7 Chunk 2 — bulk-count linked products per stock item. Same
        cost class as `_hydrate_has_image` (a single GROUP BY against
        the link table); kept as its own pass so callers can read the
        intent on the call site.

        FU-463 — built with the ORM `select()` (not raw `text()`) so
        SQLAlchemy adapts UUID bindings to whatever the column type uses
        on each engine. The original raw-SQL version silently never
        matched on SQLite because the string IDs in the IN clause didn't
        compare against the UUIDType column (see
        `project_sqlite_uuid_text_binding` memory + FU-171). Symptom was
        `linked_product_count=0` on every DTO on SQLite deployments,
        regardless of link-table contents.
        """
        if not dtos:
            return dtos
        import dataclasses
        from sqlalchemy import func, select
        from dora_api.app import db

        link_table = db.metadata.tables["StockItemProduct"]

        ids = [d.stock_item_id for d in dtos]
        stmt = (
            select(link_table.c.stock_item_id, func.count().label("n"))
            .where(link_table.c.stock_item_id.in_(ids))
            .group_by(link_table.c.stock_item_id)
        )
        rows = db.session.execute(stmt).all()

        def _key(v) -> str:
            if isinstance(v, UUID):
                return str(v)
            if isinstance(v, bytes):
                return str(UUID(bytes=v))
            return str(v)
        count_by_id = {_key(row[0]): int(row[1]) for row in rows}
        return [
            dataclasses.replace(
                d,
                linked_product_count=count_by_id.get(str(d.stock_item_id), 0),
            )
            for d in dtos
        ]

    def _hydrate_has_image(self, dtos: list[StockItemDto]) -> list[StockItemDto]:
        """C-1 Chunk 6 / FU-033 — bulk-derive `has_image` from a single SQL
        pass that never touches the deferred image blob. The flag is true
        when **either** the stock item carries its own image **or** any
        linked product carries one (the product-image fallback). Mirrors
        the get-image route's fallback rule so the SPA's "show thumbnail"
        decision matches what the bytes endpoint will actually serve.

        Built with the ORM `select()` (not raw `text()`) so SQLAlchemy
        adapts UUID bindings to whatever the column type uses on each
        engine — the original raw-SQL version silently never matched on
        SQLite because the string IDs in the IN clause didn't compare
        against the UUIDType column (`project_sqlite_uuid_text_binding`
        memory). Symptom was every row falling back to placeholder
        regardless of own/product image.
        """
        if not dtos:
            return dtos
        import dataclasses
        from sqlalchemy import case, func, literal, select
        from dora_api.app import db

        stock_item_table = db.metadata.tables["StockItem"]
        link_table = db.metadata.tables["StockItemProduct"]
        product_table = db.metadata.tables["Product"]

        ids = [d.stock_item_id for d in dtos]
        # Own-image OR (linked product with an image). LEFT JOIN keeps
        # rows that have no link rows at all (own-image only path); the
        # GROUP BY collapses the multi-product case to one row per item.
        stmt = (
            select(
                stock_item_table.c.id,
                case(
                    (stock_item_table.c.image.isnot(None), literal(1)),
                    else_=func.max(
                        case((product_table.c.image.isnot(None), literal(1)), else_=literal(0))
                    ),
                ).label("has_image"),
            )
            .select_from(
                stock_item_table
                .outerjoin(link_table, link_table.c.stock_item_id == stock_item_table.c.id)
                .outerjoin(product_table, product_table.c.id == link_table.c.product_id)
            )
            .where(stock_item_table.c.id.in_(ids))
            .group_by(stock_item_table.c.id, stock_item_table.c.image)
        )
        rows = db.session.execute(stmt).all()

        def _key(v) -> str:
            if isinstance(v, UUID):
                return str(v)
            if isinstance(v, bytes):
                return str(UUID(bytes=v))
            return str(v)
        flag_by_id = {_key(row[0]): bool(row[1]) for row in rows}
        return [
            dataclasses.replace(d, has_image=flag_by_id.get(str(d.stock_item_id), False))
            for d in dtos
        ]

    def handle(self, options) -> Page[StockItemDto]:
        import dataclasses
        page = self._base_query().paginate(
            options, StockItemDto.from_entity, field_map=_FIELD_MAP
        )
        items = self._hydrate_linked_product_count(
            self._hydrate_has_image(page.items)
        )
        return dataclasses.replace(page, items=items)

    def handle_by_id(self, stock_item_id: UUID) -> StockItemDto | None:
        entity = self._base_query().by_id(stock_item_id)
        if entity is None:
            return None
        dto = StockItemDto.from_entity(entity)
        return self._hydrate_linked_product_count(
            self._hydrate_has_image([dto])
        )[0]


@STOCK_ITEM_ROUTER.route("")
def get_stock_items():
    _Logger = logging.getLogger(__name__)
    try:
        _Options = parse_query_options(request.args)
        _Page = get_container().inject(GetStockItemsHandler).handle(_Options)
    except InvalidQueryParameter as exc:
        return bad_request(str(exc))
    _Logger.info(f"Retrieved {len(_Page.items)} of {_Page.total} stock items.")
    return paginated(_Page.items, _Page.total, _Page.page, _Page.limit)
