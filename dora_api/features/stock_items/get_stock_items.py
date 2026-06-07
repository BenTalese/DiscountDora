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

    def handle(self, options) -> Page[StockItemDto]:
        return self._base_query().paginate(
            options, StockItemDto.from_entity, field_map=_FIELD_MAP
        )

    def handle_by_id(self, stock_item_id: UUID) -> StockItemDto | None:
        entity = self._base_query().by_id(stock_item_id)
        return StockItemDto.from_entity(entity) if entity else None


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
